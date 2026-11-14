"""
BUSGO - South India Major Bus Routes, Cities, Boarding & Dropping Points Seeder
Populates the 30 major South Indian routes across TS, AP, TN, KA, KL
and hundreds of exact boarding/dropping points across Hyderabad, Chennai, Bangalore,
Vijayawada, Tirupati, Visakhapatnam, Coimbatore, Madurai, Kurnool, Kochi, Mysore.
"""

import os
from datetime import datetime, timedelta
import pymysql

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "srikar")
DB_NAME = os.getenv("DB_NAME", "busgo_db")

def init_and_seed_routes():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

    with conn.cursor() as cursor:
        print("[*] Creating relational routing tables...")

        # 1. CITIES TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            city_id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(100) NOT NULL UNIQUE,
            state_name VARCHAR(100) NOT NULL,
            latitude DECIMAL(10, 6) DEFAULT 0.0,
            longitude DECIMAL(10, 6) DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 2. ROUTES TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            route_id INT AUTO_INCREMENT PRIMARY KEY,
            source_city_id INT NOT NULL,
            destination_city_id INT NOT NULL,
            source_city VARCHAR(100) NOT NULL,
            destination_city VARCHAR(100) NOT NULL,
            source_state VARCHAR(100) NOT NULL,
            destination_state VARCHAR(100) NOT NULL,
            distance_km INT NOT NULL,
            duration VARCHAR(50) NOT NULL,
            FOREIGN KEY (source_city_id) REFERENCES cities(city_id) ON DELETE CASCADE,
            FOREIGN KEY (destination_city_id) REFERENCES cities(city_id) ON DELETE CASCADE,
            UNIQUE KEY uk_source_dest (source_city_id, destination_city_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 3. BOARDING_POINTS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS boarding_points (
            boarding_id INT AUTO_INCREMENT PRIMARY KEY,
            city_id INT NOT NULL,
            city_name VARCHAR(100) NOT NULL,
            boarding_point_name VARCHAR(150) NOT NULL,
            address VARCHAR(255) NOT NULL,
            latitude DECIMAL(10, 6) DEFAULT 0.0,
            longitude DECIMAL(10, 6) DEFAULT 0.0,
            FOREIGN KEY (city_id) REFERENCES cities(city_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 4. DROPPING_POINTS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dropping_points (
            dropping_id INT AUTO_INCREMENT PRIMARY KEY,
            city_id INT NOT NULL,
            city_name VARCHAR(100) NOT NULL,
            dropping_point_name VARCHAR(150) NOT NULL,
            address VARCHAR(255) NOT NULL,
            latitude DECIMAL(10, 6) DEFAULT 0.0,
            longitude DECIMAL(10, 6) DEFAULT 0.0,
            FOREIGN KEY (city_id) REFERENCES cities(city_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 5. BUS_OPERATORS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bus_operators (
            operator_id INT AUTO_INCREMENT PRIMARY KEY,
            operator_name VARCHAR(100) NOT NULL UNIQUE,
            bus_type VARCHAR(100) NOT NULL,
            contact_details VARCHAR(100) NOT NULL,
            rating DECIMAL(2, 1) DEFAULT 4.5
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 6. ROUTE_OPERATORS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_operators (
            id INT AUTO_INCREMENT PRIMARY KEY,
            route_id INT NOT NULL,
            operator_id INT NOT NULL,
            FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE,
            FOREIGN KEY (operator_id) REFERENCES bus_operators(operator_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Clear existing data in these route tables to re-seed cleanly
        cursor.execute("DELETE FROM route_operators;")
        cursor.execute("DELETE FROM routes;")
        cursor.execute("DELETE FROM boarding_points;")
        cursor.execute("DELETE FROM dropping_points;")
        cursor.execute("DELETE FROM bus_operators;")
        cursor.execute("DELETE FROM cities;")

        # ==============================================================
        # 1. SEED CITIES
        # ==============================================================
        print("[*] Seeding South Indian and major connecting cities...")
        cities_data = [
            ("Hyderabad", "Telangana", 17.385044, 78.486671),
            ("Bangalore", "Karnataka", 12.971599, 77.594566),
            ("Chennai", "Tamil Nadu", 13.082680, 80.270721),
            ("Vijayawada", "Andhra Pradesh", 16.506174, 80.648018),
            ("Visakhapatnam", "Andhra Pradesh", 17.686816, 83.218483),
            ("Tirupati", "Andhra Pradesh", 13.628756, 79.419174),
            ("Coimbatore", "Tamil Nadu", 11.016844, 76.955833),
            ("Madurai", "Tamil Nadu", 9.925201, 78.119774),
            ("Kochi", "Kerala", 9.931233, 76.267303),
            ("Mysore", "Karnataka", 12.295810, 76.639381),
            ("Kurnool", "Andhra Pradesh", 15.828126, 78.037270),
            ("Mumbai", "Maharashtra", 19.076090, 72.877426),
            ("Pune", "Maharashtra", 18.520430, 73.856744),
            ("Goa", "Goa", 15.299326, 74.123996),
        ]
        cursor.executemany("""
            INSERT INTO cities (city_name, state_name, latitude, longitude)
            VALUES (%s, %s, %s, %s);
        """, cities_data)

        # Build city_id lookup
        cursor.execute("SELECT city_id, city_name, state_name FROM cities;")
        city_lookup = {r["city_name"]: r for r in cursor.fetchall()}

        # ==============================================================
        # 2. SEED PREDEFINED MAJOR ROUTES (ALL CONNECTED IN BOTH DIRECTIONS)
        # ==============================================================
        print("[*] Seeding comprehensive intercity routes with bidirectional connectivity...")
        routes_spec = [
            # Original 30 South Indian corridors
            (1, "Hyderabad", "Bangalore", "TS", "KA", 570, "8h 30m"),
            (2, "Hyderabad", "Chennai", "TS", "TN", 630, "10h 30m"),
            (3, "Hyderabad", "Vijayawada", "TS", "AP", 275, "5h 15m"),
            (4, "Hyderabad", "Visakhapatnam", "TS", "AP", 620, "11h 00m"),
            (5, "Hyderabad", "Tirupati", "TS", "AP", 555, "9h 30m"),
            (6, "Chennai", "Bangalore", "TN", "KA", 345, "6h 00m"),
            (7, "Chennai", "Hyderabad", "TN", "TS", 630, "10h 30m"),
            (8, "Chennai", "Vijayawada", "TN", "AP", 450, "7h 30m"),
            (9, "Chennai", "Tirupati", "TN", "AP", 135, "3h 15m"),
            (10, "Chennai", "Coimbatore", "TN", "TN", 510, "8h 30m"),
            (11, "Bangalore", "Hyderabad", "KA", "TS", 570, "8h 30m"),
            (12, "Bangalore", "Chennai", "KA", "TN", 345, "6h 00m"),
            (13, "Bangalore", "Tirupati", "KA", "AP", 250, "4h 45m"),
            (14, "Bangalore", "Vijayawada", "KA", "AP", 660, "10h 45m"),
            (15, "Bangalore", "Coimbatore", "KA", "TN", 365, "6h 30m"),
            (16, "Vijayawada", "Hyderabad", "AP", "TS", 275, "5h 15m"),
            (17, "Vijayawada", "Chennai", "AP", "TN", 450, "7h 30m"),
            (18, "Vijayawada", "Bangalore", "AP", "KA", 660, "10h 45m"),
            (19, "Tirupati", "Chennai", "AP", "TN", 135, "3h 15m"),
            (20, "Tirupati", "Bangalore", "AP", "KA", 250, "4h 45m"),
            (21, "Tirupati", "Hyderabad", "AP", "TS", 555, "9h 30m"),
            (22, "Visakhapatnam", "Hyderabad", "AP", "TS", 620, "11h 00m"),
            (23, "Visakhapatnam", "Vijayawada", "AP", "AP", 350, "6h 00m"),
            (24, "Coimbatore", "Bangalore", "TN", "KA", 365, "6h 30m"),
            (25, "Madurai", "Chennai", "TN", "TN", 460, "7h 30m"),
            (26, "Kochi", "Bangalore", "KL", "KA", 535, "9h 30m"),
            (27, "Mysore", "Chennai", "KA", "TN", 480, "8h 15m"),
            (28, "Chennai", "Madurai", "TN", "TN", 460, "7h 30m"),
            (29, "Bangalore", "Kochi", "KA", "KL", 535, "9h 30m"),
            (30, "Hyderabad", "Kurnool", "TS", "AP", 215, "3h 45m"),

            # Complete reverse & intercity corridors for previously empty cities
            (31, "Kurnool", "Hyderabad", "AP", "TS", 215, "3h 45m"),
            (32, "Kurnool", "Bangalore", "AP", "KA", 360, "6h 00m"),
            (33, "Bangalore", "Kurnool", "KA", "AP", 360, "6h 00m"),
            (34, "Kurnool", "Tirupati", "AP", "AP", 340, "6h 00m"),
            (35, "Tirupati", "Kurnool", "AP", "AP", 340, "6h 00m"),
            (36, "Kurnool", "Vijayawada", "AP", "AP", 340, "6h 30m"),
            (37, "Vijayawada", "Kurnool", "AP", "AP", 340, "6h 30m"),

            (38, "Coimbatore", "Chennai", "TN", "TN", 510, "8h 30m"),
            (39, "Coimbatore", "Madurai", "TN", "TN", 215, "4h 15m"),
            (40, "Madurai", "Coimbatore", "TN", "TN", 215, "4h 15m"),
            (41, "Coimbatore", "Kochi", "TN", "KL", 190, "4h 00m"),
            (42, "Kochi", "Coimbatore", "KL", "TN", 190, "4h 00m"),
            (43, "Coimbatore", "Hyderabad", "TN", "TS", 720, "12h 00m"),
            (44, "Hyderabad", "Coimbatore", "TS", "TN", 720, "12h 00m"),

            (45, "Madurai", "Bangalore", "TN", "KA", 435, "7h 30m"),
            (46, "Bangalore", "Madurai", "KA", "TN", 435, "7h 30m"),
            (47, "Madurai", "Tirupati", "TN", "AP", 480, "8h 30m"),
            (48, "Tirupati", "Madurai", "AP", "TN", 480, "8h 30m"),

            (49, "Kochi", "Chennai", "KL", "TN", 680, "11h 30m"),
            (50, "Chennai", "Kochi", "TN", "KL", 680, "11h 30m"),
            (51, "Kochi", "Hyderabad", "KL", "TS", 850, "14h 30m"),
            (52, "Hyderabad", "Kochi", "TS", "KL", 850, "14h 30m"),

            (53, "Chennai", "Mysore", "TN", "KA", 480, "8h 15m"),
            (54, "Mysore", "Bangalore", "KA", "KA", 145, "2h 45m"),
            (55, "Bangalore", "Mysore", "KA", "KA", 145, "2h 45m"),
            (56, "Mysore", "Hyderabad", "KA", "TS", 715, "11h 45m"),
            (57, "Hyderabad", "Mysore", "TS", "KA", 715, "11h 45m"),
            (58, "Mysore", "Coimbatore", "KA", "TN", 205, "4h 30m"),
            (59, "Coimbatore", "Mysore", "TN", "KA", 205, "4h 30m"),

            (60, "Vijayawada", "Visakhapatnam", "AP", "AP", 350, "6h 00m"),
            (61, "Visakhapatnam", "Chennai", "AP", "TN", 800, "13h 30m"),
            (62, "Chennai", "Visakhapatnam", "TN", "AP", 800, "13h 30m"),
            (63, "Visakhapatnam", "Bangalore", "AP", "KA", 1010, "16h 00m"),
            (64, "Bangalore", "Visakhapatnam", "KA", "AP", 1010, "16h 00m"),
            (65, "Visakhapatnam", "Tirupati", "AP", "AP", 750, "12h 30m"),
            (66, "Tirupati", "Visakhapatnam", "AP", "AP", 750, "12h 30m"),

            (67, "Vijayawada", "Tirupati", "AP", "AP", 380, "6h 30m"),
            (68, "Tirupati", "Vijayawada", "AP", "AP", 380, "6h 30m"),

            # Major Connecting Metros (Mumbai, Pune, Goa)
            (69, "Mumbai", "Pune", "MH", "MH", 150, "3h 30m"),
            (70, "Pune", "Mumbai", "MH", "MH", 150, "3h 30m"),
            (71, "Mumbai", "Goa", "MH", "GA", 580, "10h 30m"),
            (72, "Goa", "Mumbai", "GA", "MH", 580, "10h 30m"),
            (73, "Mumbai", "Hyderabad", "MH", "TS", 710, "11h 30m"),
            (74, "Hyderabad", "Mumbai", "TS", "MH", 710, "11h 30m"),
            (75, "Mumbai", "Bangalore", "MH", "KA", 980, "15h 30m"),
            (76, "Bangalore", "Mumbai", "KA", "MH", 980, "15h 30m"),
            (77, "Pune", "Hyderabad", "MH", "TS", 560, "9h 00m"),
            (78, "Hyderabad", "Pune", "TS", "MH", 560, "9h 00m"),
            (79, "Pune", "Bangalore", "MH", "KA", 840, "13h 00m"),
            (80, "Bangalore", "Pune", "KA", "MH", 840, "13h 00m"),
            (81, "Goa", "Bangalore", "GA", "KA", 560, "9h 30m"),
            (82, "Bangalore", "Goa", "KA", "GA", 560, "9h 30m"),
            (83, "Goa", "Hyderabad", "GA", "TS", 660, "11h 00m"),
            (84, "Hyderabad", "Goa", "TS", "GA", 660, "11h 00m"),
        ]

        routes_rows = []
        for s_no, src, dst, s_st, d_st, dist, dur in routes_spec:
            src_obj = city_lookup.get(src)
            dst_obj = city_lookup.get(dst)
            if src_obj and dst_obj:
                routes_rows.append((
                    src_obj["city_id"], dst_obj["city_id"],
                    src, dst,
                    src_obj["state_name"], dst_obj["state_name"],
                    dist, dur
                ))

        cursor.executemany("""
            INSERT INTO routes (
                source_city_id, destination_city_id, source_city, destination_city,
                source_state, destination_state, distance_km, duration
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, routes_rows)

        # ==============================================================
        # 3. SEED BOARDING & DROPPING POINTS FOR THE 8+ MAJOR CITIES
        # ==============================================================
        print("[*] Seeding comprehensive boarding and dropping points...")

        # A. HYDERABAD (20 Points)
        hyd_points = [
            ("MGBS – Mahatma Gandhi Bus Station", "Gowliguda Central, Hyderabad", 17.3789, 78.4812),
            ("JBS – Jubilee Bus Station", "Secunderabad Main, Hyderabad", 17.4475, 78.4996),
            ("Kukatpally", "Near Metro Station, Mumbai Highway", 17.4933, 78.3995),
            ("Miyapur", "Allwyn X Roads, Metro Station", 17.4968, 78.3614),
            ("Ameerpet", "Near Big Bazaar & Metro Pillar A1023", 17.4375, 78.4482),
            ("SR Nagar", "Sanjeeva Reddy Nagar X Roads", 17.4435, 78.4441),
            ("LB Nagar", "Near Kamineni Hospital & Ring Road", 17.3457, 78.5522),
            ("Dilsukhnagar", "Near Konark Theatre / Metro Pillar", 17.3688, 78.5247),
            ("Uppal", "Uppal Ring Road Junction", 17.3984, 78.5583),
            ("Gachibowli", "ORR Junction, Near Outer Ring Road", 17.4401, 78.3489),
            ("Hitech City", "Cyber Towers / Shilparamam", 17.4504, 78.3808),
            ("Kondapur", "Near RTO Office / Botanical Garden", 17.4699, 78.3578),
            ("Mehdipatnam", "PVNR Expressway Pillar 62", 17.3916, 78.4398),
            ("Lakdikapul", "Near Police Station / Assembly", 17.4048, 78.4633),
            ("Shamshabad", "Airport Toll Plaza, NH44", 17.2543, 78.4311),
            ("Aramghar", "Aramghar X Roads, National Highway 44", 17.3195, 78.4391),
            ("KPHB", "KPHB Colony Metro Station, Phase 1", 17.4891, 78.4035),
            ("ESI", "ESI Hospital Bus Stop, Sanath Nagar", 17.4481, 78.4385),
            ("Miyapur X Roads", "Near Talkie Town, Miyapur Junction", 17.4981, 78.3639),
            ("Vanasthalipuram", "Rythu Bazar, Sagar Ring Road", 17.3312, 78.5721),
        ]

        # B. CHENNAI (25 Points)
        chn_points = [
            ("Koyambedu – CMBT", "Omni Bus Stand, CMBT Gate 3", 13.0694, 80.1948),
            ("Chennai Central", "Wall Tax Road / Central Railway Station", 13.0827, 80.2757),
            ("Chennai Egmore", "Egmore Railway Station North Gate", 13.0784, 80.2608),
            ("Madhavaram", "Madhavaram Mofussil Bus Terminus (MMBT)", 13.1489, 80.2314),
            ("Tambaram", "Tambaram Railway Station West Gate, GST Road", 12.9249, 80.1000),
            ("Perungalathur", "Near High School & GST Highway", 12.9048, 80.0883),
            ("Guduvancheri", "Guduvancheri Bus Stand, GST Road", 12.8465, 80.0617),
            ("Vandalur", "Vandalur Zoo Junction, NH45", 12.8906, 80.0811),
            ("Chromepet", "Near MIT Flyover & Bus Stop", 12.9516, 80.1462),
            ("Pallavaram", "Near Pallavaram Flyover, GST Road", 12.9675, 80.1491),
            ("Guindy", "Guindy Kathipara Junction & Metro", 13.0067, 80.2025),
            ("Vadapalani", "Near Vadapalani Murugan Temple / Metro", 13.0500, 80.2121),
            ("Anna Nagar", "Roundtana / Blue Star Metro", 13.0850, 80.2101),
            ("Porur", "Porur Toll Gate / DLF IT Park", 13.0382, 80.1565),
            ("Poonamallee", "Poonamallee Bus Terminus, Bypass", 13.0473, 80.0945),
            ("Ambattur", "Ambattur OT Bus Stand & Estate", 13.1143, 80.1548),
            ("Avadi", "Avadi Checkpost / Railway Station", 13.1147, 80.1011),
            ("T Nagar", "Panagal Park / Usman Road", 13.0418, 80.2341),
            ("Velachery", "Vijayanagar Bus Terminus, Velachery", 12.9759, 80.2212),
            ("Sholinganallur", "OMR Toll Plaza / IT Corridor Junction", 12.9010, 80.2279),
            ("Thoraipakkam", "OMR Toll Gate / Jain College", 12.9416, 80.2362),
            ("Perungudi", "Perungudi Toll Gate, OMR Road", 12.9654, 80.2461),
            ("Navalur", "Navalur Toll Plaza, Vivira Mall", 12.8478, 80.2269),
            ("Siruseri", "SIPCOT IT Park Entrance, OMR", 12.8289, 80.2185),
            ("Kelambakkam", "Kelambakkam Bus Stand, ECR-OMR Link", 12.7874, 80.2184),
        ]

        # C. BANGALORE (25 Points)
        blr_points = [
            ("Majestic – Kempegowda Bus Station", "Platform 18/19, Majestic Terminal", 12.9767, 77.5713),
            ("Satellite Bus Stand", "Mysore Road, Bapuji Nagar", 12.9542, 77.5401),
            ("Electronic City", "Toll Gate Phase 1, Elevated Flyover", 12.8452, 77.6602),
            ("Silk Board", "Central Silk Board Junction, Hosur Road", 12.9176, 77.6238),
            ("Madiwala", "Near Total Mall / St. John's Hospital", 12.9226, 77.6174),
            ("Marathahalli", "Near Multiplex & Outer Ring Road Bridge", 12.9591, 77.6974),
            ("Whitefield", "ITPL Main Gate, Hope Farm Junction", 12.9698, 77.7499),
            ("KR Puram", "Hanging Bridge / Tin Factory Junction", 13.0075, 77.6959),
            ("Tin Factory", "K.R. Puram Flyover Toll Plaza", 13.0033, 77.6681),
            ("Hebbal", "Esteem Mall Flyover, Airport Road", 13.0358, 77.5970),
            ("Yeshwanthpur", "Near Govardhan Theatre / Railway Station", 13.0280, 77.5409),
            ("HSR Layout", "HSR BDA Complex, 27th Main Road", 12.9121, 77.6446),
            ("Bellandur", "Central Mall, Outer Ring Road", 12.9260, 77.6762),
            ("Bommanahalli", "Near Oxford College, Hosur Road", 12.9081, 77.6241),
            ("Bommasandra", "Bommasandra Industrial Area, Toll Gate", 12.8167, 77.6917),
            ("Attibele", "Attibele Toll Plaza, Karnataka-TN Border", 12.7794, 77.7711),
            ("Sarjapur", "Sarjapur Circle / Wipro Campus Gate", 12.8601, 77.7850),
            ("Devanahalli", "Near Toll Plaza, Kempegowda Airport Road", 13.2483, 77.7126),
            ("Yelahanka", "Yelahanka Police Station / NES Bus Stop", 13.1007, 77.5963),
            ("Anand Rao Circle", "VRL / SRS Office, Anand Rao Circle", 12.9811, 77.5750),
            ("Indiranagar", "CMH Road / 100 Feet Road Junction", 12.9784, 77.6408),
            ("Vijayanagar", "Vijayanagar TTMC Bus Station", 12.9698, 77.5362),
            ("Banashankari", "Banashankari Bus Stand / Temple", 12.9155, 77.5736),
            ("Hosakerehalli", "NICE Road Toll Plaza", 12.9250, 77.5270),
            ("BTM Layout", "BTM 2nd Stage, Udupi Garden Signal", 12.9166, 77.6101),
        ]

        # D. VIJAYAWADA (15 Points)
        vja_points = [
            ("Benz Circle", "MG Road & Bandar Road Junction", 16.4975, 80.6558),
            ("Pandit Nehru Bus Station (PNBS)", "Central RTC Terminal, Krishna River Bank", 16.5085, 80.6158),
            ("Ramavarappadu Ring Road", "Eluru Road Junction, Ramavarappadu", 16.5189, 80.6811),
            ("Enikepadu", "Enikepadu Center, NH16 Highway", 16.5312, 80.7025),
            ("Gannavaram", "Airport Entrance, National Highway 16", 16.5375, 80.7961),
            ("Auto Nagar", "Auto Nagar Gate, Bandar Road", 16.4950, 80.6710),
            ("Poranki", "Poranki Center, Machilipatnam Highway", 16.4789, 80.7011),
            ("Kanuru", "VR Siddhartha Engineering College Road", 16.4880, 80.6900),
            ("Mangalagiri", "Mangalagiri Bypass Junction, NH16", 16.4350, 80.5600),
            ("Tadepalli", "Prakasam Barrage Road, Tadepalli", 16.4812, 80.6080),
            ("Varadhi", "Krishna River Bridge Entrance", 16.4958, 80.6200),
            ("Patamata", "Patamata High School Road", 16.5020, 80.6650),
            ("Nidamanuru", "Nidamanuru Toll Plaza", 16.5410, 80.7250),
            ("Kankipadu", "Kankipadu Bus Stand, Bandar Road", 16.4250, 80.7810),
            ("Ibrahimpatnam", "Ibrahimpatnam Ring Center, Hyderabad Highway", 16.5850, 80.5250),
        ]

        # E. TIRUPATI (10 Points)
        tpt_points = [
            ("Tirupati RTC Bus Stand", "Central Bus Station, Railway Road", 13.6288, 79.4250),
            ("Railway Station", "Tirupati Main Railway Station Gate", 13.6350, 79.4180),
            ("Leela Mahal Circle", "Alipiri Bypass Road", 13.6420, 79.4210),
            ("RTO Office", "Tirupati Urban RTO Junction", 13.6210, 79.4080),
            ("Karakambadi", "Karakambadi Road Junction", 13.6550, 79.4600),
            ("Renigunta", "Renigunta Junction / Airport Road", 13.6500, 79.5100),
            ("Tiruchanoor", "Padmavathi Temple Road", 13.6150, 79.4500),
            ("Alipiri", "Tirumala Footpath Toll Gate", 13.6600, 79.4000),
            ("Kapila Theertham", "Near Sacred Waterfalls & Temple", 13.6520, 79.4120),
            ("Srinivasa Mangapuram", "Kalyana Venkateswara Temple Highway", 13.6180, 79.3190),
        ]

        # F. VISAKHAPATNAM (10 Points)
        viz_points = [
            ("RTC Complex", "Dwaraka Bus Station, Central Vizag", 17.7265, 83.3035),
            ("Maddilapalem", "Andhra University Gate / Maddilapalem Junction", 17.7340, 83.3240),
            ("NAD Junction", "NAD Flyover, Airport Road", 17.7450, 83.2180),
            ("Gajuwaka", "Old Gajuwaka Junction, Industrial Hub", 17.6950, 83.2100),
            ("Kurmannapalem", "Steel Plant Toll Plaza, NH16", 17.6780, 83.1750),
            ("MVP Colony", "MVP Double Road / Sector 3", 17.7420, 83.3380),
            ("Akkayyapalem", "Highway Junction, Akkayyapalem", 17.7300, 83.2950),
            ("Simhachalam", "Simhachalam Hill Road Entrance", 17.7680, 83.2450),
            ("Anakapalle", "Anakapalle Bypass Toll Gate", 17.6910, 83.0030),
            ("Lankelapalem", "Pharma City Junction, NH16", 17.6650, 83.1250),
        ]

        # G. COIMBATORE (10 Points)
        cbe_points = [
            ("Gandhipuram", "Central Omni Bus Stand, Cross Cut Road", 11.0180, 76.9660),
            ("Singanallur", "Singanallur Bus Terminal, Trichy Road", 10.9980, 77.0250),
            ("Ukkadam", "Ukkadam Bus Stand, Pollachi Road", 10.9900, 76.9600),
            ("Omni Bus Stand", "Sathy Road, Near New Bus Stand", 11.0250, 76.9750),
            ("Peelamedu", "Near PSG College of Technology", 11.0280, 77.0050),
            ("Hopes College", "Avinashi Road Flyover", 11.0330, 77.0200),
            ("Avinashi Road", "Near KMCH Hospital & Airport Junction", 11.0420, 77.0450),
            ("Sulur", "Sulur Air Force Station Junction", 11.0250, 77.1250),
            ("Saravanampatti", "IT Corridor / CHIL SEZ", 11.0800, 76.9950),
            ("Gandhipuram Town Bus Stand", "Gandhipuram Local Transit Center", 11.0170, 76.9680),
        ]

        # H. MADURAI (10 Points)
        mdu_points = [
            ("Mattuthavani Bus Stand", "Integrated Bus Terminus (MIBT)", 9.9450, 78.1650),
            ("Periyar Bus Stand", "Near Central Railway Station", 9.9180, 78.1120),
            ("Arappalayam", "Arappalayam Cross Bus Stand", 9.9320, 78.1050),
            ("Kalavasal", "Theni Road Flyover, Kalavasal", 9.9280, 78.0950),
            ("Thirunagar", "GST Road, Thirunagar Stop", 9.8750, 78.0650),
            ("Tirupparankundram", "Murugan Temple Hill Entrance", 9.8820, 78.0710),
            ("Othakadai", "Trichy Highway / High Court Bench", 9.9650, 78.1950),
            ("Fatima College", "Dindigul Road Bypass", 9.9450, 78.1020),
            ("Kappalur", "Kappalur Toll Plaza, South Bypass", 9.8450, 78.0350),
            ("Melur", "Melur Bus Stand, Chennai Highway", 10.0250, 78.3350),
        ]

        # Additional cities (Kurnool, Kochi, Mysore)
        knl_points = [
            ("Kurnool RTC Bus Stand", "Central RTC Station, Bellary Road", 15.8281, 78.0372),
            ("Checkpost", "Tungabhadra Bridge Checkpost", 15.8450, 78.0450),
            ("Collectorate", "Near District Court & Collector Office", 15.8200, 78.0300),
        ]
        cok_points = [
            ("Vyttila Mobility Hub", "Vyttila Central Terminal, Kochi", 9.9680, 76.3190),
            ("Palarivattom", "Palarivattom Bypass Flyover", 10.0050, 76.3100),
            ("Edappally", "Lulu Mall / Toll Gate Metro", 10.0250, 76.3080),
            ("Aluva", "Near Aluva Metro & Railway Station", 10.1080, 76.3550),
        ]
        mys_points = [
            ("Mysore KSRTC Bus Stand", "Suburban Bus Stand, Central Mysore", 12.3110, 76.6550),
            ("Palace Gate", "Near Mysore Palace South Gate", 12.3020, 76.6550),
            ("Columbia Asia Junction", "Bangalore-Mysore Highway Ring Road", 12.3550, 76.6650),
        ]
        mum_points = [
            ("Borivali West", "Near Gokul Hotel / Western Express Highway", 19.2307, 72.8567),
            ("Andheri East", "Near Western Express Highway Metro", 19.1136, 72.8697),
            ("Sion Central", "Chunabhatti Flyover, Sion Circle", 19.0400, 72.8640),
            ("Vashi", "Old Toll Plaza, Vashi Highway", 19.0770, 72.9980),
            ("Dadar TT Circle", "Swami Gyan Jivandas Marg, Dadar East", 19.0180, 72.8430),
            ("Thane", "Teen Hath Naka, Eastern Express Highway", 19.1860, 72.9750),
        ]
        pun_points = [
            ("Swargate", "Swargate ST Bus Stand, Pune", 18.5018, 73.8580),
            ("Wakad", "Hinjewadi Bridge / Wakad Flyover", 18.5980, 73.7650),
            ("Hinjewadi Phase 1", "Infosys Circle / Shivaji Chowk", 18.5910, 73.7380),
            ("Shivajinagar", "Near Railway Station / Sancheti Hospital", 18.5310, 73.8440),
            ("Viman Nagar", "Near Phoenix Marketcity, Nagar Road", 18.5670, 73.9140),
        ]
        goa_points = [
            ("Panaji Kadam Bus Stand", "Central KTC Bus Stand, Panaji", 15.4989, 73.8278),
            ("Mapusa", "Mapusa KTC Bus Stand, North Goa", 15.5920, 73.8150),
            ("Margao", "Margao KTC Bus Terminal, South Goa", 15.2830, 73.9660),
            ("Vasco da Gama", "Near Railway Station, Vasco", 15.3980, 73.8110),
        ]

        all_cities_points = {
            "Hyderabad": hyd_points,
            "Chennai": chn_points,
            "Bangalore": blr_points,
            "Vijayawada": vja_points,
            "Tirupati": tpt_points,
            "Visakhapatnam": viz_points,
            "Coimbatore": cbe_points,
            "Madurai": mdu_points,
            "Kurnool": knl_points,
            "Kochi": cok_points,
            "Mysore": mys_points,
            "Mumbai": mum_points,
            "Pune": pun_points,
            "Goa": goa_points,
        }

        boarding_rows = []
        dropping_rows = []

        for city_name, points in all_cities_points.items():
            c_info = city_lookup.get(city_name)
            if not c_info:
                continue
            c_id = c_info["city_id"]
            for name, addr, lat, lng in points:
                boarding_rows.append((c_id, city_name, name, addr, lat, lng))
                dropping_rows.append((c_id, city_name, name, addr, lat, lng))

        cursor.executemany("""
            INSERT INTO boarding_points (city_id, city_name, boarding_point_name, address, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, boarding_rows)

        cursor.executemany("""
            INSERT INTO dropping_points (city_id, city_name, dropping_point_name, address, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, dropping_rows)

        print(f"[+] Inserted {len(boarding_rows)} Boarding Points and {len(dropping_rows)} Dropping Points across {len(all_cities_points)} cities!")

        # ==============================================================
        # 4. SEED BUS OPERATORS
        # ==============================================================
        print("[*] Seeding official bus operators...")
        operators_data = [
            ("APSRTC (Amaravati / Garuda)", "Multi-Axle Volvo AC Sleeper", "1800-200-2001", 4.6),
            ("TSRTC (Rajadhani / Garuda)", "Super Luxury AC Seater (2+2)", "1800-599-9599", 4.5),
            ("KSRTC (Airavat Club Class)", "Multi-Axle Volvo I-Shift AC", "080-49596666", 4.7),
            ("SETC (Tamil Nadu State)", "Ultra Deluxe Non-AC Seater", "044-24794707", 4.2),
            ("Orange Travels", "BharatBenz AC Sleeper (2+1)", "040-33559999", 4.8),
            ("VRL Travels", "Multi-Axle I-Shift AC Sleeper", "0836-2307300", 4.9),
            ("SRS Travels", "Scania AC Sleeper (2+1)", "080-26809000", 4.4),
            ("IntrCity SmartBus", "AC Sleeper & Smart Lounge", "1800-120-120", 4.7),
            ("Zingbus", "Electric & AC Sleeper (2+1)", "1800-103-3456", 4.7),
            ("Kaveri Travels", "Multi-Axle AC Sleeper", "040-23232323", 4.6),
            ("Morning Star Travels", "Non-AC Sleeper & AC Seater", "0866-2494949", 4.3),
            ("KPN Travels", "AC Sleeper & Seater", "0427-2444444", 4.4),
            ("Parveen Travels", "AC Semi-Sleeper & Volvo", "044-49004900", 4.5),
            ("Jabbar Travels", "AC Sleeper (2+1)", "040-24654321", 4.4),
            ("Greenline Travels", "Scania AC Sleeper (2+1)", "080-22221111", 4.6),
        ]
        cursor.executemany("""
            INSERT INTO bus_operators (operator_name, bus_type, contact_details, rating)
            VALUES (%s, %s, %s, %s);
        """, operators_data)

        # Build operator_id lookup
        cursor.execute("SELECT operator_id, operator_name FROM bus_operators;")
        op_lookup = {r["operator_name"]: r["operator_id"] for r in cursor.fetchall()}

        # Build route_id lookup
        cursor.execute("SELECT route_id, source_city, destination_city FROM routes;")
        route_lookup = {(r["source_city"], r["destination_city"]): r["route_id"] for r in cursor.fetchall()}

        # Link routes to operators
        route_ops = []
        for (src, dst), r_id in route_lookup.items():
            for op_name, op_id in op_lookup.items():
                route_ops.append((r_id, op_id))
        cursor.executemany("""
            INSERT INTO route_operators (route_id, operator_id) VALUES (%s, %s);
        """, route_ops)
        print(f"[+] Linked {len(route_ops)} route-operator corridors.")

        # ==============================================================
        # 5. SYNC BUSES TABLE: 30 ROUTES WITH LOWER COST TO HIGH COST
        # ==============================================================
        print("[*] Generating active bus schedules for all 30 routes for next 30 days...")
        cursor.execute("DELETE FROM seat_reservations;")
        cursor.execute("DELETE FROM bookings;")
        cursor.execute("DELETE FROM buses;")
        cursor.execute("ALTER TABLE buses AUTO_INCREMENT = 1;")

        # Fare templates for each route: budget -> mid -> luxury
        bus_schedule_templates = []

        # Common operator tier builder for any route
        def get_route_tiers(dist):
            if dist < 200:
                return [
                    ("State RTC Express", "Non-AC Seater (2+2)", max(150.0, round(dist * 1.3, 0)), 3.9, 6, 0),
                    ("Morning Star Travels", "AC Seater (2+2)", max(250.0, round(dist * 2.0, 0)), 4.3, 9, 30),
                    ("KPN Travels", "AC Sleeper (2+1)", max(380.0, round(dist * 2.8, 0)), 4.5, 21, 0),
                    ("IntrCity SmartBus", "AC Sleeper (2+1)", max(450.0, round(dist * 3.2, 0)), 4.7, 22, 15),
                ]
            elif dist < 400:
                return [
                    ("State RTC Garuda", "Non-AC Seater (2+2)", max(299.0, round(dist * 1.1, 0)), 4.0, 7, 0),
                    ("Parveen Travels", "AC Seater (2+2)", max(450.0, round(dist * 1.5, 0)), 4.4, 14, 30),
                    ("Orange Travels", "AC Sleeper (2+1)", max(650.0, round(dist * 2.1, 0)), 4.7, 21, 30),
                    ("VRL Travels", "Multi-Axle Volvo AC Sleeper", max(850.0, round(dist * 2.6, 0)), 4.9, 22, 30),
                ]
            else:
                return [
                    ("State RTC Rajadhani", "Non-AC Seater (2+2)", max(499.0, round(dist * 0.95, 0)), 4.0, 18, 0),
                    ("Morning Star Travels", "Non-AC Sleeper (2+1)", max(680.0, round(dist * 1.25, 0)), 4.2, 19, 15),
                    ("IntrCity SmartBus", "AC Seater (2+2)", max(750.0, round(dist * 1.45, 0)), 4.6, 18, 30),
                    ("Zingbus", "AC Sleeper (2+1)", max(899.0, round(dist * 1.70, 0)), 4.7, 21, 0),
                    ("Orange Travels", "Multi-Axle Volvo AC Sleeper", max(1099.0, round(dist * 2.0, 0)), 4.8, 20, 30),
                    ("VRL Travels", "BharatBenz AC Sleeper (2+1)", max(1299.0, round(dist * 2.3, 0)), 4.9, 21, 45),
                ]

        now = datetime.now()
        bus_rows = []

        for s_no, src, dst, s_st, d_st, dist, dur_str in routes_spec:
            # parse duration hours
            dur_parts = dur_str.split('h')
            dur_hrs = float(dur_parts[0].strip()) + (float(dur_parts[1].replace('m', '').strip()) / 60.0 if len(dur_parts) > 1 else 0.0)
            tiers = get_route_tiers(dist)

            for day_offset in range(0, 30):
                trip_date = now.date() + timedelta(days=day_offset)
                for op_name, b_type, price, rating, dep_h, dep_m in tiers:
                    dep_dt = datetime(trip_date.year, trip_date.month, trip_date.day, dep_h, dep_m)
                    arr_dt = dep_dt + timedelta(hours=dur_hrs)
                    facilities = "WiFi, Charging Point, Reading Light, Live GPS Tracking, Blankets" if "AC" in b_type else "Charging Point, Emergency Hammer, Reading Light"
                    bus_rows.append((
                        op_name,
                        src,
                        dst,
                        dep_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        arr_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        b_type,
                        price,
                        30,
                        36,
                        facilities,
                        rating
                    ))

        cursor.executemany("""
            INSERT INTO buses (
                operator_name, source, destination, departure_time, arrival_time,
                bus_type, price, available_seats, total_seats, facilities, rating
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, bus_rows)

        print(f"[+] Successfully seeded {len(bus_rows)} active schedules for all 30 routes over 30 days!")

    conn.close()
    print("=== SOUTH INDIA ROUTES AND BUSES DATABASE SEED COMPLETE ===")

if __name__ == "__main__":
    init_and_seed_routes()
