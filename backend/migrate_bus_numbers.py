import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from init_db import get_connection

STATE_PREFIXES = {
    "chennai": "TN-01",
    "coimbatore": "TN-38",
    "madurai": "TN-58",
    "salem": "TN-30",
    "trichy": "TN-45",
    "tirunelveli": "TN-72",
    "vellore": "TN-23",
    "bangalore": "KA-01",
    "mysore": "KA-09",
    "mangalore": "KA-19",
    "hubli": "KA-25",
    "belgaum": "KA-22",
    "hyderabad": "TS-09",
    "warangal": "TS-03",
    "nizamabad": "TS-16",
    "karimnagar": "TS-02",
    "vijayawada": "AP-16",
    "visakhapatnam": "AP-31",
    "tirupati": "AP-03",
    "guntur": "AP-07",
    "kurnool": "AP-21",
    "mumbai": "MH-01",
    "pune": "MH-12",
    "nagpur": "MH-31",
    "nashik": "MH-15",
    "kochi": "KL-07",
    "trivandrum": "KL-01",
    "calicut": "KL-11",
    "delhi": "DL-01",
    "jaipur": "RJ-14"
}

SERIES_LETTERS = ["AN", "BZ", "EX", "KL", "PR", "UB", "VT", "WX", "ZZ", "FD"]

def migrate_and_populate():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Add column if it doesn't exist
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'busgo_db' 
                  AND TABLE_NAME = 'buses' 
                  AND COLUMN_NAME = 'bus_number';
            """)
            exists = cur.fetchone()['count'] > 0
            if not exists:
                print("[*] Adding bus_number column to buses table...")
                cur.execute("ALTER TABLE buses ADD COLUMN bus_number VARCHAR(50) DEFAULT NULL;")
                print("[+] Column bus_number added.")
            else:
                print("[i] bus_number column already exists.")

            # 2. Check if bookings table also has bus_number or add it for redundancy
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'busgo_db' 
                  AND TABLE_NAME = 'bookings' 
                  AND COLUMN_NAME = 'bus_number';
            """)
            b_exists = cur.fetchone()['count'] > 0
            if not b_exists:
                print("[*] Adding bus_number column to bookings table...")
                cur.execute("ALTER TABLE bookings ADD COLUMN bus_number VARCHAR(50) DEFAULT NULL;")
                print("[+] Column bus_number added to bookings.")

            # 3. Fetch all buses and populate bus_number
            cur.execute("SELECT bus_id, source, operator_name FROM buses;")
            buses = cur.fetchall()
            print(f"[*] Found {len(buses)} buses to populate with realistic bus numbers...")

            updates = []
            for b in buses:
                b_id = b["bus_id"]
                src = (b["source"] or "").strip().lower()
                prefix = STATE_PREFIXES.get(src, "IN-09")
                series = SERIES_LETTERS[b_id % len(SERIES_LETTERS)]
                num_part = f"{(b_id % 9000) + 1000}"
                bus_number = f"{prefix}-{series}-{num_part}"
                updates.append((bus_number, b_id))

            print("[*] Updating buses in batches...")
            cur.executemany("UPDATE buses SET bus_number = %s WHERE bus_id = %s;", updates)
            print(f"[+] Successfully updated {len(updates)} buses with unique bus numbers!")

            # 4. Also update existing bookings with bus_number from their associated bus
            cur.execute("""
                UPDATE bookings b
                JOIN buses bus ON b.bus_id = bus.bus_id
                SET b.bus_number = bus.bus_number
                WHERE b.bus_number IS NULL OR b.bus_number = '';
            """)
            print("[+] Updated existing bookings with their bus numbers.")

            # 5. Sample check
            cur.execute("SELECT bus_id, operator_name, source, destination, bus_number, price FROM buses LIMIT 5;")
            for row in cur.fetchall():
                print("Sample Bus:", row)

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_and_populate()
