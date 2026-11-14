"""
BUSGO Database Schema and Seeding Manager
Implements MySQL database design according to SRS Section 9:
- TABLE 1: USERS
- TABLE 2: BUSES
- TABLE 3: BOOKINGS
- TABLE 4: CHAT_HISTORY
- TABLE 5: TRAVEL_KNOWLEDGE
- Plus SEAT_LAYOUT and REVIEWS for RedBus-style rich interaction.
"""

import os
import pymysql
import hashlib
from datetime import datetime, timedelta

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "srikar")
DB_NAME = os.getenv("DB_NAME", "busgo_db")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection(use_database=True):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if use_database else None,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


def initialize_database():
    print(f"[*] Initializing MySQL database '{DB_NAME}' on {DB_HOST}:{DB_PORT}...")
    
    # 1. Create database if it doesn't exist
    root_conn = get_connection(use_database=False)
    with root_conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    root_conn.close()

    # 2. Connect to the database and create tables
    conn = get_connection(use_database=True)
    with conn.cursor() as cursor:
        # Table 1: USERS (SRS Table 1)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            phone VARCHAR(20) DEFAULT '',
            role ENUM('customer', 'operator', 'admin') DEFAULT 'customer',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Table 2: BUSES (SRS Table 2)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            bus_id INT AUTO_INCREMENT PRIMARY KEY,
            operator_name VARCHAR(100) NOT NULL,
            source VARCHAR(100) NOT NULL,
            destination VARCHAR(100) NOT NULL,
            departure_time DATETIME NOT NULL,
            arrival_time DATETIME NOT NULL,
            bus_type VARCHAR(50) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            available_seats INT NOT NULL DEFAULT 36,
            total_seats INT NOT NULL DEFAULT 36,
            facilities TEXT,
            rating DECIMAL(2,1) DEFAULT 4.5,
            bus_number VARCHAR(50) DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_source_dest (source, destination),
            INDEX idx_bus_type (bus_type),
            INDEX idx_price (price)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Table 3: BOOKINGS (SRS Table 3)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            bus_id INT NOT NULL,
            passenger_name VARCHAR(100) NOT NULL,
            passenger_age INT DEFAULT 28,
            passenger_gender VARCHAR(10) DEFAULT 'Male',
            passenger_email VARCHAR(100) DEFAULT '',
            passenger_phone VARCHAR(20) DEFAULT '',
            seat_number VARCHAR(100) NOT NULL,
            boarding_point VARCHAR(255) DEFAULT NULL,
            dropping_point VARCHAR(255) DEFAULT NULL,
            bus_number VARCHAR(50) DEFAULT NULL,
            booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            booking_status VARCHAR(30) DEFAULT 'CONFIRMED',
            total_fare DECIMAL(10,2) DEFAULT 0.00,
            pnr_number VARCHAR(30) UNIQUE,
            payment_status VARCHAR(30) DEFAULT 'COMPLETED',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (bus_id) REFERENCES buses(bus_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Table 4: CHAT_HISTORY (SRS Table 4)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            tool_called VARCHAR(100) NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Table 5: TRAVEL_KNOWLEDGE (SRS Table 5)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_knowledge (
            document_id INT AUTO_INCREMENT PRIMARY KEY,
            document_name VARCHAR(255) NOT NULL,
            document_type VARCHAR(100) NOT NULL,
            content_preview TEXT,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Auxiliary Table: SEAT_RESERVATIONS (Tracks individual occupied seats per bus)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seat_reservations (
            reservation_id INT AUTO_INCREMENT PRIMARY KEY,
            bus_id INT NOT NULL,
            seat_number VARCHAR(10) NOT NULL,
            deck ENUM('lower', 'upper') DEFAULT 'lower',
            seat_type ENUM('sleeper', 'seater') DEFAULT 'sleeper',
            is_booked TINYINT(1) DEFAULT 1,
            is_ladies TINYINT(1) DEFAULT 0,
            booking_id INT NULL,
            FOREIGN KEY (bus_id) REFERENCES buses(bus_id) ON DELETE CASCADE,
            UNIQUE KEY uq_bus_seat (bus_id, seat_number)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

    print("[+] Database tables successfully created.")
    seed_data(conn)
    conn.close()


def seed_data(conn):
    with conn.cursor() as cursor:
        # Check if users already seeded
        cursor.execute("SELECT COUNT(*) AS count FROM users;")
        if cursor.fetchone()['count'] == 0:
            print("[*] Seeding default users...")
            default_users = [
                ("Admin", "admin@busgo.com", hash_password("admin123"), "9876543210", "admin"),
                ("Srikar Reddy", "srikar@busgo.com", hash_password("srikar123"), "9123456780", "customer"),
                ("Sharma Travels", "sharma@busgo.com", hash_password("operator123"), "9988776655", "operator"),
                ("Test Passenger", "passenger@busgo.com", hash_password("pass123"), "9000011111", "customer")
            ]
            cursor.executemany(
                "INSERT INTO users (username, email, password_hash, phone, role) VALUES (%s, %s, %s, %s, %s)",
                default_users
            )

        # Check if buses already seeded
        cursor.execute("SELECT COUNT(*) AS count FROM buses;")
        if cursor.fetchone()['count'] == 0:
            print("[*] Seeding sample buses and routes...")
            try:
                from seed_more_buses import seed_all_buses
                seed_all_buses()
            except Exception as e:
                print(f"[!] Warning seeding buses: {e}")
                bus_templates = [
                    # Hyderabad -> Bangalore
                    {
                    "operator_name": "Orange Travels",
                    "source": "Hyderabad",
                    "destination": "Bangalore",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 950.00,
                    "facilities": "WiFi, Charging Point, Blankets, Water Bottle, Live Tracking, Reading Light",
                    "dep_hour": 21, "dep_min": 0, "duration_hours": 9, "rating": 4.8
                },
                {
                    "operator_name": "VRL Travels",
                    "source": "Hyderabad",
                    "destination": "Bangalore",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 1200.00,
                    "facilities": "WiFi, USB Charging, Pillows, Blankets, Water Bottle, Emergency Exit, GPS",
                    "dep_hour": 22, "dep_min": 30, "duration_hours": 8.5, "rating": 4.9
                },
                {
                    "operator_name": "SRS Travels",
                    "source": "Hyderabad",
                    "destination": "Bangalore",
                    "bus_type": "Non-AC Sleeper (2+1)",
                    "price": 750.00,
                    "facilities": "Charging Point, Reading Light, Emergency Hammer",
                    "dep_hour": 20, "dep_min": 15, "duration_hours": 9.5, "rating": 4.3
                },
                {
                    "operator_name": "IntrCity SmartBus",
                    "source": "Hyderabad",
                    "destination": "Bangalore",
                    "bus_type": "AC Seater (2+2)",
                    "price": 699.00,
                    "facilities": "WiFi, Reclining Seats, USB Charging, Live Tracking, Air Suspension",
                    "dep_hour": 18, "dep_min": 0, "duration_hours": 9, "rating": 4.6
                },
                {
                    "operator_name": "Zingbus",
                    "source": "Hyderabad",
                    "destination": "Bangalore",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 899.00,
                    "facilities": "WiFi, Premium Lounge, Blankets, Water Bottle, CCTV",
                    "dep_hour": 23, "dep_min": 15, "duration_hours": 8, "rating": 4.7
                },

                # Bangalore -> Hyderabad
                {
                    "operator_name": "Orange Travels",
                    "source": "Bangalore",
                    "destination": "Hyderabad",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 999.00,
                    "facilities": "WiFi, Charging Point, Blankets, Water Bottle, Live Tracking",
                    "dep_hour": 21, "dep_min": 30, "duration_hours": 9, "rating": 4.8
                },
                {
                    "operator_name": "VRL Travels",
                    "source": "Bangalore",
                    "destination": "Hyderabad",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 1250.00,
                    "facilities": "WiFi, USB Charging, Blankets, Water Bottle, GPS",
                    "dep_hour": 22, "dep_min": 0, "duration_hours": 8.5, "rating": 4.9
                },

                # Mumbai -> Pune
                {
                    "operator_name": "Neeta Tours & Travels",
                    "source": "Mumbai",
                    "destination": "Pune",
                    "bus_type": "AC Seater (2+2)",
                    "price": 380.00,
                    "facilities": "Reclining Seats, AC, Charging Point, Water Bottle",
                    "dep_hour": 6, "dep_min": 0, "duration_hours": 3.5, "rating": 4.5
                },
                {
                    "operator_name": "Purple Travels",
                    "source": "Mumbai",
                    "destination": "Pune",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 550.00,
                    "facilities": "WiFi, Reading Light, Charging Point, Air Suspension",
                    "dep_hour": 23, "dep_min": 0, "duration_hours": 4, "rating": 4.6
                },

                # Pune -> Mumbai
                {
                    "operator_name": "Neeta Tours & Travels",
                    "source": "Pune",
                    "destination": "Mumbai",
                    "bus_type": "AC Seater (2+2)",
                    "price": 400.00,
                    "facilities": "Reclining Seats, AC, Charging Point, Water Bottle",
                    "dep_hour": 7, "dep_min": 30, "duration_hours": 3.5, "rating": 4.4
                },

                # Delhi -> Jaipur
                {
                    "operator_name": "Zingbus",
                    "source": "Delhi",
                    "destination": "Jaipur",
                    "bus_type": "AC Seater (2+2)",
                    "price": 499.00,
                    "facilities": "WiFi, Reclining Seats, Charging Point, Live Tracking",
                    "dep_hour": 6, "dep_min": 30, "duration_hours": 5, "rating": 4.7
                },
                {
                    "operator_name": "Goldline Super Deluxe",
                    "source": "Delhi",
                    "destination": "Jaipur",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 750.00,
                    "facilities": "Blankets, Mineral Water, Reading Light, Charging Point",
                    "dep_hour": 23, "dep_min": 30, "duration_hours": 5.5, "rating": 4.5
                },

                # Chennai -> Bangalore
                {
                    "operator_name": "IntrCity SmartBus",
                    "source": "Chennai",
                    "destination": "Bangalore",
                    "bus_type": "AC Sleeper (2+1)",
                    "price": 850.00,
                    "facilities": "WiFi, Lounge Access, Blankets, USB Charging, GPS",
                    "dep_hour": 22, "dep_min": 15, "duration_hours": 6.5, "rating": 4.8
                },
                {
                    "operator_name": "KPN Travels",
                    "source": "Chennai",
                    "destination": "Bangalore",
                    "bus_type": "Non-AC Sleeper (2+1)",
                    "price": 599.00,
                    "facilities": "Charging Point, Reading Light, Emergency Hammer",
                    "dep_hour": 21, "dep_min": 0, "duration_hours": 7, "rating": 4.2
                }
            ]

            bus_rows = []
            for day_offset in range(0, 15):
                trip_date = now.date() + timedelta(days=day_offset)
                for t in bus_templates:
                    dep_dt = datetime(trip_date.year, trip_date.month, trip_date.day, t["dep_hour"], t["dep_min"])
                    arr_dt = dep_dt + timedelta(hours=t["duration_hours"])
                    bus_rows.append((
                        t["operator_name"],
                        t["source"],
                        t["destination"],
                        dep_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        arr_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        t["bus_type"],
                        t["price"],
                        30,  # available_seats
                        36,  # total_seats
                        t["facilities"],
                        t["rating"]
                    ))

            cursor.executemany("""
                INSERT INTO buses (
                    operator_name, source, destination, departure_time, arrival_time,
                    bus_type, price, available_seats, total_seats, facilities, rating
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, bus_rows)
            print(f"[+] Successfully seeded {len(bus_rows)} buses across 15 travel dates.")

        # Seed initial sample seat reservations for each bus
        cursor.execute("SELECT bus_id, bus_type FROM buses LIMIT 20;")
        sample_buses = cursor.fetchall()
        for b in sample_buses:
            b_id = b['bus_id']
            # Pre-seed some occupied seats: L2, L5, U3, U7
            occupied_seats = [
                (b_id, "L1", "lower", "sleeper", 0, 0),
                (b_id, "L2", "lower", "sleeper", 1, 1), # booked for lady
                (b_id, "L3", "lower", "sleeper", 0, 0),
                (b_id, "L4", "lower", "sleeper", 0, 0),
                (b_id, "L5", "lower", "sleeper", 1, 0), # booked
                (b_id, "U1", "upper", "sleeper", 0, 0),
                (b_id, "U2", "upper", "sleeper", 0, 0),
                (b_id, "U3", "upper", "sleeper", 1, 0), # booked
                (b_id, "U4", "upper", "sleeper", 0, 0),
            ]
            cursor.executemany("""
                INSERT IGNORE INTO seat_reservations 
                (bus_id, seat_number, deck, seat_type, is_booked, is_ladies)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, occupied_seats)

        # Seed initial travel knowledge documents in MySQL metadata (SRS Table 5)
        cursor.execute("SELECT COUNT(*) AS count FROM travel_knowledge;")
        if cursor.fetchone()['count'] == 0:
            knowledge_docs = [
                ("Cancellation and Refund Policy", "Policy Document", "Detailed rules for bus ticket cancellation, refund percentage slabs based on hours prior to departure, and refund processing timelines."),
                ("Booking & Ticketing FAQs", "FAQ Document", "Frequently asked questions regarding PNR generation, payment options, child fares, senior citizen concessions, and booking modification."),
                ("Luggage & Baggage Guidelines", "Guidelines Document", "Allowable passenger baggage weight (15 kg per seat), extra luggage charges, restricted and hazardous articles on long-distance buses."),
                ("Seat Selection & Deck Guide", "Guide Document", "Differences between lower and upper deck berths, window vs single aisle seats, and exclusive female reservation policies."),
                ("Passenger Boarding Guidelines", "Guidelines Document", "Required government ID proofs for travel, boarding reporting times, bus amenities guidelines, and safety protocols.")
            ]
            cursor.executemany("""
                INSERT INTO travel_knowledge (document_name, document_type, content_preview)
                VALUES (%s, %s, %s)
            """, knowledge_docs)
            print("[+] Seeded travel knowledge document metadata.")


if __name__ == "__main__":
    initialize_database()
