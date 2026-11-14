"""
BUSGO Comprehensive Bus Fleet & Routes Expansion Seeder
All major Indian intercity bus routes with budget-to-premium pricing.
Covers 36+ route corridors across 18 cities with 120+ operator templates.
"""

import os
from datetime import datetime, timedelta
import pymysql

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "srikar")
DB_NAME = os.getenv("DB_NAME", "busgo_db")

def seed_all_buses():
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
        print("[*] Clearing old bus schedules to populate full new fleet...")
        cursor.execute("DELETE FROM bookings;")
        cursor.execute("DELETE FROM seat_reservations;")
        cursor.execute("DELETE FROM buses;")
        cursor.execute("ALTER TABLE buses AUTO_INCREMENT = 1;")

        # ==============================================================
        # ROUTES CATALOG — ordered LOW to HIGH price within each route
        # ==============================================================
        routes_catalog = [

            # ==========================================================
            # 1. CHENNAI -> HYDERABAD  (~630 km, 10-11h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda Plus", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "Non-AC Seater (2+2)", "price": 550.00,
             "facilities": "Reclining Seats, Reading Light", "dep_hour": 18, "dep_min": 30, "duration_hours": 11, "rating": 3.9},
            {"operator_name": "Morning Star Travels", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 699.00,
             "facilities": "USB Charging, Reading Light, Emergency Hammer", "dep_hour": 19, "dep_min": 30, "duration_hours": 11, "rating": 4.2},
            {"operator_name": "SRE Travels", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 750.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 18, "dep_min": 0, "duration_hours": 10.5, "rating": 4.3},
            {"operator_name": "IntrCity SmartBus", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 799.00,
             "facilities": "WiFi, Smart Lounge Access, Reclining Seats, USB Charging", "dep_hour": 17, "dep_min": 30, "duration_hours": 10.5, "rating": 4.6},
            {"operator_name": "Kaveri Travels", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 999.00,
             "facilities": "Charging Point, Reading Lamp, Blankets, Water Bottle", "dep_hour": 21, "dep_min": 45, "duration_hours": 10, "rating": 4.6},
            {"operator_name": "Jabbar Travels", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 1050.00,
             "facilities": "WiFi, Charging Point, Blankets, CCTV Security", "dep_hour": 22, "dep_min": 30, "duration_hours": 9.5, "rating": 4.5},
            {"operator_name": "Orange Travels", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1150.00,
             "facilities": "WiFi, Charging Point, Blankets, Mineral Water, GPS Tracking, Reading Light", "dep_hour": 20, "dep_min": 30, "duration_hours": 10, "rating": 4.8},
            {"operator_name": "VRL Travels", "source": "Chennai", "destination": "Hyderabad",
             "bus_type": "BharatBenz AC Sleeper (2+1)", "price": 1350.00,
             "facilities": "WiFi, USB Ports, Air Suspension, Emergency Exit, Pillows, Blankets", "dep_hour": 21, "dep_min": 15, "duration_hours": 10, "rating": 4.9},

            # ==========================================================
            # 2. HYDERABAD -> CHENNAI  (~630 km, 10-11h)
            # ==========================================================
            {"operator_name": "TSRTC Rajadhani", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "Non-AC Seater (2+2)", "price": 520.00,
             "facilities": "Reclining Seats, Fan, Emergency Window", "dep_hour": 18, "dep_min": 0, "duration_hours": 11, "rating": 3.8},
            {"operator_name": "Morning Star Travels", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 680.00,
             "facilities": "USB Charging, Reading Light, Emergency Hammer", "dep_hour": 19, "dep_min": 15, "duration_hours": 11, "rating": 4.2},
            {"operator_name": "IntrCity SmartBus", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "AC Seater (2+2)", "price": 740.00,
             "facilities": "WiFi, Smart Lounge Access, Reclining Seats, USB Charging", "dep_hour": 18, "dep_min": 30, "duration_hours": 10.5, "rating": 4.6},
            {"operator_name": "Kaveri Travels", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 950.00,
             "facilities": "Charging Point, Reading Lamp, Blankets, Water Bottle", "dep_hour": 21, "dep_min": 30, "duration_hours": 10, "rating": 4.6},
            {"operator_name": "KPN Travels", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 1020.00,
             "facilities": "WiFi, Charging Point, Blankets, CCTV Security", "dep_hour": 22, "dep_min": 15, "duration_hours": 10, "rating": 4.5},
            {"operator_name": "Orange Travels", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1199.00,
             "facilities": "WiFi, Charging Point, Blankets, Mineral Water, GPS Tracking, Reading Light", "dep_hour": 20, "dep_min": 0, "duration_hours": 10, "rating": 4.8},
            {"operator_name": "VRL Travels", "source": "Hyderabad", "destination": "Chennai",
             "bus_type": "BharatBenz AC Sleeper (2+1)", "price": 1380.00,
             "facilities": "WiFi, USB Ports, Air Suspension, Emergency Exit, Pillows, Blankets", "dep_hour": 21, "dep_min": 0, "duration_hours": 10, "rating": 4.9},

            # ==========================================================
            # 3. HYDERABAD -> BANGALORE  (~570 km, 8-9h)
            # ==========================================================
            {"operator_name": "KSRTC Flybus", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 499.00,
             "facilities": "Reclining Seats, Fan, Emergency Window", "dep_hour": 18, "dep_min": 0, "duration_hours": 9.5, "rating": 3.9},
            {"operator_name": "National Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 650.00,
             "facilities": "Reading Light, Charging Point, Emergency Hammer", "dep_hour": 19, "dep_min": 30, "duration_hours": 9, "rating": 4.1},
            {"operator_name": "IntrCity SmartBus", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 699.00,
             "facilities": "WiFi, Reclining Seats, USB Charging, Live Tracking, Air Suspension", "dep_hour": 17, "dep_min": 30, "duration_hours": 8.5, "rating": 4.6},
            {"operator_name": "SRS Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 750.00,
             "facilities": "Charging Point, Reading Light, Emergency Hammer", "dep_hour": 20, "dep_min": 15, "duration_hours": 9, "rating": 4.3},
            {"operator_name": "Morning Star Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "AC Seater / Sleeper", "price": 820.00,
             "facilities": "Charging Point, Reading Lamp, Water Bottle", "dep_hour": 20, "dep_min": 45, "duration_hours": 8.5, "rating": 4.4},
            {"operator_name": "Zingbus", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 899.00,
             "facilities": "WiFi, Premium Lounge, Blankets, Water Bottle, CCTV", "dep_hour": 23, "dep_min": 15, "duration_hours": 7.5, "rating": 4.7},
            {"operator_name": "Orange Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 950.00,
             "facilities": "WiFi, Charging Point, Blankets, Water Bottle, Live Tracking, Reading Light", "dep_hour": 21, "dep_min": 0, "duration_hours": 8.5, "rating": 4.8},
            {"operator_name": "Jabbar Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 1050.00,
             "facilities": "Charging Point, Clean Blankets, Water Bottle, CCTV", "dep_hour": 21, "dep_min": 45, "duration_hours": 8, "rating": 4.5},
            {"operator_name": "Kaveri Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1199.00,
             "facilities": "WiFi, Charging Socket, Luxury Bedding, Live GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 8, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Hyderabad", "destination": "Bangalore",
             "bus_type": "Multi-Axle I-Shift AC Sleeper (2+1)", "price": 1350.00,
             "facilities": "WiFi, USB Charging, Pillows, Blankets, Water Bottle, Emergency Exit, GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 8, "rating": 4.9},

            # ==========================================================
            # 4. BANGALORE -> HYDERABAD  (~570 km, 8-9h)
            # ==========================================================
            {"operator_name": "KSRTC Flybus", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "Non-AC Seater (2+2)", "price": 480.00,
             "facilities": "Reclining Seats, Fan, Emergency Window", "dep_hour": 18, "dep_min": 30, "duration_hours": 9.5, "rating": 3.9},
            {"operator_name": "National Travels", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 640.00,
             "facilities": "Reading Light, Charging Point, Emergency Hammer", "dep_hour": 19, "dep_min": 0, "duration_hours": 9, "rating": 4.1},
            {"operator_name": "IntrCity SmartBus", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 680.00,
             "facilities": "WiFi, Reclining Seats, USB Charging, Live Tracking", "dep_hour": 17, "dep_min": 30, "duration_hours": 8.5, "rating": 4.6},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 760.00,
             "facilities": "Charging Point, Reading Light, Emergency Hammer", "dep_hour": 20, "dep_min": 30, "duration_hours": 9, "rating": 4.3},
            {"operator_name": "Zingbus", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 880.00,
             "facilities": "WiFi, Blankets, Water Bottle, CCTV", "dep_hour": 23, "dep_min": 0, "duration_hours": 7.5, "rating": 4.7},
            {"operator_name": "Jabbar Travels", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 970.00,
             "facilities": "Charging Point, Clean Blankets, Water Bottle, CCTV", "dep_hour": 21, "dep_min": 15, "duration_hours": 8, "rating": 4.5},
            {"operator_name": "Orange Travels", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 990.00,
             "facilities": "WiFi, Charging Point, Blankets, Water Bottle, Live Tracking", "dep_hour": 21, "dep_min": 30, "duration_hours": 8.5, "rating": 4.8},
            {"operator_name": "Kaveri Travels", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1100.00,
             "facilities": "WiFi, Charging Socket, Luxury Bedding, Live GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 8, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Hyderabad",
             "bus_type": "Multi-Axle I-Shift AC Sleeper (2+1)", "price": 1350.00,
             "facilities": "WiFi, USB Charging, Blankets, Water Bottle, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 8, "rating": 4.9},

            # ==========================================================
            # 5. CHENNAI -> BANGALORE  (~350 km, 5.5-7h)
            # ==========================================================
            {"operator_name": "Parveen Travels", "source": "Chennai", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 350.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 7, "dep_min": 0, "duration_hours": 6.5, "rating": 3.8},
            {"operator_name": "Asian Xpress", "source": "Chennai", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 499.00,
             "facilities": "AC, Reclining Seats, Charging Point, Water Bottle", "dep_hour": 14, "dep_min": 30, "duration_hours": 5.5, "rating": 4.5},
            {"operator_name": "KPN Travels", "source": "Chennai", "destination": "Bangalore",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 599.00,
             "facilities": "Charging Point, Reading Light, Emergency Hammer", "dep_hour": 21, "dep_min": 0, "duration_hours": 6.5, "rating": 4.2},
            {"operator_name": "Greenline Travels", "source": "Chennai", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 750.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 0, "duration_hours": 6, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Chennai", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 850.00,
             "facilities": "WiFi, Lounge Access, Blankets, USB Charging, GPS", "dep_hour": 22, "dep_min": 15, "duration_hours": 6, "rating": 4.8},

            # ==========================================================
            # 6. BANGALORE -> CHENNAI  (~350 km, 5.5-7h)
            # ==========================================================
            {"operator_name": "Parveen Travels", "source": "Bangalore", "destination": "Chennai",
             "bus_type": "Non-AC Seater (2+2)", "price": 360.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 30, "duration_hours": 6.5, "rating": 3.8},
            {"operator_name": "KPN Travels", "source": "Bangalore", "destination": "Chennai",
             "bus_type": "AC Seater (2+2)", "price": 520.00,
             "facilities": "AC, Pushback Seats, USB Charging", "dep_hour": 15, "dep_min": 0, "duration_hours": 5.5, "rating": 4.3},
            {"operator_name": "Asian Xpress", "source": "Bangalore", "destination": "Chennai",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 580.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 21, "dep_min": 0, "duration_hours": 6.5, "rating": 4.1},
            {"operator_name": "Greenline Travels", "source": "Bangalore", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 780.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 30, "duration_hours": 6, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Bangalore", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 890.00,
             "facilities": "WiFi, Lounge Access, Blankets, USB Charging, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 6, "rating": 4.8},

            # ==========================================================
            # 7. MUMBAI -> PUNE  (~150 km, 3-4h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Mumbai", "destination": "Pune",
             "bus_type": "Non-AC Seater (2+2)", "price": 250.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 30, "duration_hours": 4, "rating": 3.8},
            {"operator_name": "Neeta Tours & Travels", "source": "Mumbai", "destination": "Pune",
             "bus_type": "AC Seater (2+2)", "price": 380.00,
             "facilities": "Reclining Seats, AC, Charging Point, Water Bottle", "dep_hour": 7, "dep_min": 0, "duration_hours": 3.5, "rating": 4.5},
            {"operator_name": "Shrinath Travels", "source": "Mumbai", "destination": "Pune",
             "bus_type": "AC Seater (2+2)", "price": 420.00,
             "facilities": "AC, USB Charging, Water Bottle, Live GPS", "dep_hour": 10, "dep_min": 0, "duration_hours": 3.5, "rating": 4.4},
            {"operator_name": "Purple Travels", "source": "Mumbai", "destination": "Pune",
             "bus_type": "AC Sleeper (2+1)", "price": 550.00,
             "facilities": "WiFi, Reading Light, Charging Point, Air Suspension", "dep_hour": 23, "dep_min": 0, "duration_hours": 3.5, "rating": 4.6},

            # ==========================================================
            # 8. PUNE -> MUMBAI  (~150 km, 3-4h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Pune", "destination": "Mumbai",
             "bus_type": "Non-AC Seater (2+2)", "price": 260.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 0, "duration_hours": 4, "rating": 3.8},
            {"operator_name": "Neeta Tours & Travels", "source": "Pune", "destination": "Mumbai",
             "bus_type": "AC Seater (2+2)", "price": 400.00,
             "facilities": "Reclining Seats, AC, Charging Point, Water Bottle", "dep_hour": 7, "dep_min": 30, "duration_hours": 3.5, "rating": 4.4},
            {"operator_name": "Shrinath Travels", "source": "Pune", "destination": "Mumbai",
             "bus_type": "AC Seater (2+2)", "price": 430.00,
             "facilities": "AC, USB Charging, Water Bottle, Live GPS", "dep_hour": 14, "dep_min": 0, "duration_hours": 3.5, "rating": 4.4},
            {"operator_name": "Purple Travels", "source": "Pune", "destination": "Mumbai",
             "bus_type": "AC Sleeper (2+1)", "price": 570.00,
             "facilities": "WiFi, Reading Light, Charging Point, Air Suspension", "dep_hour": 22, "dep_min": 30, "duration_hours": 3.5, "rating": 4.6},

            # ==========================================================
            # 9. MUMBAI -> GOA  (~590 km, 11-12h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Mumbai", "destination": "Goa",
             "bus_type": "Non-AC Seater (2+2)", "price": 750.00,
             "facilities": "Fan, Reclining Seats, Emergency Window", "dep_hour": 18, "dep_min": 0, "duration_hours": 12, "rating": 3.9},
            {"operator_name": "Paulo Travels", "source": "Mumbai", "destination": "Goa",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 950.00,
             "facilities": "Charging Point, Reading Light, Water Bottle", "dep_hour": 19, "dep_min": 0, "duration_hours": 11.5, "rating": 4.3},
            {"operator_name": "Zingbus", "source": "Mumbai", "destination": "Goa",
             "bus_type": "AC Sleeper (2+1)", "price": 1250.00,
             "facilities": "WiFi, Blankets, Charging Point, Mineral Water, Live GPS", "dep_hour": 20, "dep_min": 0, "duration_hours": 11, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Mumbai", "destination": "Goa",
             "bus_type": "Multi-Axle Volvo AC Sleeper", "price": 1550.00,
             "facilities": "WiFi, Luxury Pillows, Air Suspension, Emergency Exit", "dep_hour": 21, "dep_min": 30, "duration_hours": 11, "rating": 4.9},

            # ==========================================================
            # 10. GOA -> MUMBAI  (~590 km, 11-12h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Goa", "destination": "Mumbai",
             "bus_type": "Non-AC Seater (2+2)", "price": 780.00,
             "facilities": "Fan, Reclining Seats, Emergency Window", "dep_hour": 17, "dep_min": 30, "duration_hours": 12, "rating": 3.9},
            {"operator_name": "Paulo Travels", "source": "Goa", "destination": "Mumbai",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 980.00,
             "facilities": "Charging Point, Reading Light, Water Bottle", "dep_hour": 18, "dep_min": 30, "duration_hours": 11.5, "rating": 4.3},
            {"operator_name": "Zingbus", "source": "Goa", "destination": "Mumbai",
             "bus_type": "AC Sleeper (2+1)", "price": 1290.00,
             "facilities": "WiFi, Blankets, Charging Point, Mineral Water, Live GPS", "dep_hour": 19, "dep_min": 30, "duration_hours": 11, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Goa", "destination": "Mumbai",
             "bus_type": "Multi-Axle Volvo AC Sleeper", "price": 1590.00,
             "facilities": "WiFi, Luxury Pillows, Air Suspension, Emergency Exit", "dep_hour": 20, "dep_min": 45, "duration_hours": 11, "rating": 4.9},

            # ==========================================================
            # 11. HYDERABAD -> VIJAYAWADA  (~275 km, 5-6h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda", "source": "Hyderabad", "destination": "Vijayawada",
             "bus_type": "Non-AC Seater (2+2)", "price": 320.00,
             "facilities": "Reclining Seats, Fan", "dep_hour": 8, "dep_min": 0, "duration_hours": 5.5, "rating": 3.9},
            {"operator_name": "Morning Star Travels", "source": "Hyderabad", "destination": "Vijayawada",
             "bus_type": "AC Seater (2+2)", "price": 450.00,
             "facilities": "Reclining Seats, USB Charging, AC", "dep_hour": 15, "dep_min": 0, "duration_hours": 5, "rating": 4.5},
            {"operator_name": "Orange Travels", "source": "Hyderabad", "destination": "Vijayawada",
             "bus_type": "AC Sleeper (2+1)", "price": 650.00,
             "facilities": "WiFi, Charging Socket, Blanket, Water Bottle", "dep_hour": 23, "dep_min": 0, "duration_hours": 5, "rating": 4.8},

            # ==========================================================
            # 12. VIJAYAWADA -> HYDERABAD  (~275 km, 5-6h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda", "source": "Vijayawada", "destination": "Hyderabad",
             "bus_type": "Non-AC Seater (2+2)", "price": 330.00,
             "facilities": "Reclining Seats, Fan", "dep_hour": 7, "dep_min": 30, "duration_hours": 5.5, "rating": 3.9},
            {"operator_name": "Sri Krishna Travels", "source": "Vijayawada", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 480.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 14, "dep_min": 0, "duration_hours": 5, "rating": 4.4},
            {"operator_name": "Orange Travels", "source": "Vijayawada", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 680.00,
             "facilities": "WiFi, Charging Socket, Blanket, Water Bottle", "dep_hour": 23, "dep_min": 30, "duration_hours": 5, "rating": 4.8},

            # ==========================================================
            # 13. HYDERABAD -> VISAKHAPATNAM  (~620 km, 10-11h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda Plus", "source": "Hyderabad", "destination": "Visakhapatnam",
             "bus_type": "Non-AC Seater (2+2)", "price": 650.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 18, "dep_min": 0, "duration_hours": 11, "rating": 3.9},
            {"operator_name": "Sri Krishna Travels", "source": "Hyderabad", "destination": "Visakhapatnam",
             "bus_type": "AC Seater (2+2)", "price": 850.00,
             "facilities": "AC, USB Charging, Water Bottle, Reading Light", "dep_hour": 19, "dep_min": 0, "duration_hours": 8.5, "rating": 4.3},
            {"operator_name": "Kaveri Travels", "source": "Hyderabad", "destination": "Visakhapatnam",
             "bus_type": "Multi-Axle AC Sleeper", "price": 1200.00,
             "facilities": "WiFi, Luxury Berths, Water Bottle, Blankets, GPS", "dep_hour": 20, "dep_min": 15, "duration_hours": 10.5, "rating": 4.7},

            # ==========================================================
            # 14. VISAKHAPATNAM -> HYDERABAD  (~620 km, 10-11h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda Plus", "source": "Visakhapatnam", "destination": "Hyderabad",
             "bus_type": "Non-AC Seater (2+2)", "price": 680.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 17, "dep_min": 30, "duration_hours": 11, "rating": 3.9},
            {"operator_name": "Sri Krishna Travels", "source": "Visakhapatnam", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 880.00,
             "facilities": "AC, USB Charging, Water Bottle, Reading Light", "dep_hour": 18, "dep_min": 30, "duration_hours": 8.5, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Visakhapatnam", "destination": "Hyderabad",
             "bus_type": "Multi-Axle AC Sleeper", "price": 1250.00,
             "facilities": "WiFi, Luxury Berths, Water Bottle, Blankets, GPS", "dep_hour": 19, "dep_min": 45, "duration_hours": 10.5, "rating": 4.8},

            # ==========================================================
            # 15. DELHI -> JAIPUR  (~280 km, 5-6h)
            # ==========================================================
            {"operator_name": "RSRTC Volvo", "source": "Delhi", "destination": "Jaipur",
             "bus_type": "Non-AC Seater (2+2)", "price": 350.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 0, "duration_hours": 5.5, "rating": 3.9},
            {"operator_name": "Zingbus", "source": "Delhi", "destination": "Jaipur",
             "bus_type": "AC Seater (2+2)", "price": 499.00,
             "facilities": "WiFi, Reclining Seats, Charging Point, Live Tracking", "dep_hour": 7, "dep_min": 0, "duration_hours": 5, "rating": 4.7},
            {"operator_name": "IntrCity SmartBus", "source": "Delhi", "destination": "Jaipur",
             "bus_type": "AC Sleeper (2+1)", "price": 650.00,
             "facilities": "WiFi, Lounge, Blankets, USB Charging", "dep_hour": 22, "dep_min": 0, "duration_hours": 5.5, "rating": 4.7},
            {"operator_name": "Goldline Super Deluxe", "source": "Delhi", "destination": "Jaipur",
             "bus_type": "AC Sleeper (2+1)", "price": 799.00,
             "facilities": "Blankets, Mineral Water, Reading Light, Charging Point", "dep_hour": 23, "dep_min": 30, "duration_hours": 5.5, "rating": 4.5},

            # ==========================================================
            # 16. JAIPUR -> DELHI  (~280 km, 5-6h)
            # ==========================================================
            {"operator_name": "RSRTC Volvo", "source": "Jaipur", "destination": "Delhi",
             "bus_type": "Non-AC Seater (2+2)", "price": 360.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 30, "duration_hours": 5.5, "rating": 3.9},
            {"operator_name": "Zingbus", "source": "Jaipur", "destination": "Delhi",
             "bus_type": "AC Seater (2+2)", "price": 520.00,
             "facilities": "WiFi, Reclining Seats, Charging Point, Live Tracking", "dep_hour": 16, "dep_min": 0, "duration_hours": 5, "rating": 4.7},
            {"operator_name": "IntrCity SmartBus", "source": "Jaipur", "destination": "Delhi",
             "bus_type": "AC Sleeper (2+1)", "price": 680.00,
             "facilities": "WiFi, Lounge, Blankets, USB Charging", "dep_hour": 22, "dep_min": 30, "duration_hours": 5.5, "rating": 4.7},
            {"operator_name": "Goldline Super Deluxe", "source": "Jaipur", "destination": "Delhi",
             "bus_type": "AC Sleeper (2+1)", "price": 820.00,
             "facilities": "Blankets, Mineral Water, Reading Light, Charging Point", "dep_hour": 23, "dep_min": 0, "duration_hours": 5.5, "rating": 4.5},

            # ==========================================================
            # 17. DELHI -> CHANDIGARH  (~250 km, 4.5-5h)
            # ==========================================================
            {"operator_name": "HRTC Volvo", "source": "Delhi", "destination": "Chandigarh",
             "bus_type": "Non-AC Seater (2+2)", "price": 300.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 0, "duration_hours": 5, "rating": 3.9},
            {"operator_name": "Zingbus", "source": "Delhi", "destination": "Chandigarh",
             "bus_type": "AC Seater (2+2)", "price": 450.00,
             "facilities": "WiFi, USB Charging, Reclining Seats", "dep_hour": 7, "dep_min": 0, "duration_hours": 4.5, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Delhi", "destination": "Chandigarh",
             "bus_type": "AC Sleeper (2+1)", "price": 650.00,
             "facilities": "WiFi, Lounge, Blankets, USB Charging", "dep_hour": 23, "dep_min": 0, "duration_hours": 5, "rating": 4.7},

            # ==========================================================
            # 18. CHANDIGARH -> DELHI  (~250 km, 4.5-5h)
            # ==========================================================
            {"operator_name": "HRTC Volvo", "source": "Chandigarh", "destination": "Delhi",
             "bus_type": "Non-AC Seater (2+2)", "price": 310.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 30, "duration_hours": 5, "rating": 3.9},
            {"operator_name": "Zingbus", "source": "Chandigarh", "destination": "Delhi",
             "bus_type": "AC Seater (2+2)", "price": 480.00,
             "facilities": "WiFi, USB Charging, Reclining Seats", "dep_hour": 15, "dep_min": 30, "duration_hours": 4.5, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Chandigarh", "destination": "Delhi",
             "bus_type": "AC Sleeper (2+1)", "price": 680.00,
             "facilities": "WiFi, Lounge, Blankets, USB Charging", "dep_hour": 22, "dep_min": 0, "duration_hours": 5, "rating": 4.7},

            # ==========================================================
            # 19. PUNE -> HYDERABAD  (~560 km, 9-10h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Pune", "destination": "Hyderabad",
             "bus_type": "Non-AC Seater (2+2)", "price": 550.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 18, "dep_min": 0, "duration_hours": 10, "rating": 3.9},
            {"operator_name": "National Travels", "source": "Pune", "destination": "Hyderabad",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 720.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 19, "dep_min": 30, "duration_hours": 9.5, "rating": 4.2},
            {"operator_name": "VRL Travels", "source": "Pune", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 950.00,
             "facilities": "WiFi, Charging Point, Blankets, GPS", "dep_hour": 21, "dep_min": 0, "duration_hours": 9, "rating": 4.8},
            {"operator_name": "Orange Travels", "source": "Pune", "destination": "Hyderabad",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1250.00,
             "facilities": "WiFi, Blankets, Pillows, USB Charging, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 9, "rating": 4.9},

            # ==========================================================
            # 20. HYDERABAD -> PUNE  (~560 km, 9-10h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Hyderabad", "destination": "Pune",
             "bus_type": "Non-AC Seater (2+2)", "price": 580.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 18, "dep_min": 30, "duration_hours": 10, "rating": 3.9},
            {"operator_name": "National Travels", "source": "Hyderabad", "destination": "Pune",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 750.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 19, "dep_min": 0, "duration_hours": 9.5, "rating": 4.2},
            {"operator_name": "Orange Travels", "source": "Hyderabad", "destination": "Pune",
             "bus_type": "AC Sleeper (2+1)", "price": 980.00,
             "facilities": "WiFi, Charging Point, Blankets, Water Bottle", "dep_hour": 21, "dep_min": 30, "duration_hours": 9, "rating": 4.8},
            {"operator_name": "VRL Travels", "source": "Hyderabad", "destination": "Pune",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1280.00,
             "facilities": "WiFi, Blankets, Pillows, USB Charging, GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 9, "rating": 4.9},

            # ==========================================================
            # 21. BANGALORE -> GOA  (~560 km, 10-12h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Bangalore", "destination": "Goa",
             "bus_type": "Non-AC Seater (2+2)", "price": 650.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 18, "dep_min": 30, "duration_hours": 12, "rating": 3.9},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Goa",
             "bus_type": "AC Sleeper (2+1)", "price": 1100.00,
             "facilities": "WiFi, Air Suspension, Blankets, Water Bottle", "dep_hour": 21, "dep_min": 45, "duration_hours": 11, "rating": 4.6},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Goa",
             "bus_type": "Multi-Axle Volvo AC Sleeper", "price": 1450.00,
             "facilities": "WiFi, Luxury Pillows, Air Suspension, Emergency Exit", "dep_hour": 22, "dep_min": 0, "duration_hours": 10.5, "rating": 4.9},

            # ==========================================================
            # 22. GOA -> BANGALORE  (~560 km, 10-12h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Goa", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 680.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 17, "dep_min": 30, "duration_hours": 12, "rating": 3.9},
            {"operator_name": "SRS Travels", "source": "Goa", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 1150.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 20, "dep_min": 0, "duration_hours": 11, "rating": 4.6},
            {"operator_name": "VRL Travels", "source": "Goa", "destination": "Bangalore",
             "bus_type": "Multi-Axle AC Sleeper", "price": 1480.00,
             "facilities": "WiFi, Blankets, Pillows, USB Charging", "dep_hour": 20, "dep_min": 30, "duration_hours": 10.5, "rating": 4.9},

            # ==========================================================
            # 23. MUMBAI -> BANGALORE  (~980 km, 15-17h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Mumbai", "destination": "Bangalore",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 850.00,
             "facilities": "Charging Point, Reading Light, Emergency Hammer", "dep_hour": 16, "dep_min": 0, "duration_hours": 16, "rating": 4.0},
            {"operator_name": "Paulo Travels", "source": "Mumbai", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 999.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 17, "dep_min": 0, "duration_hours": 15, "rating": 4.3},
            {"operator_name": "SRS Travels", "source": "Mumbai", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 1350.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, CCTV", "dep_hour": 18, "dep_min": 0, "duration_hours": 15, "rating": 4.6},
            {"operator_name": "VRL Travels", "source": "Mumbai", "destination": "Bangalore",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1750.00,
             "facilities": "WiFi, Luxury Pillows, Blankets, GPS, Air Suspension", "dep_hour": 18, "dep_min": 30, "duration_hours": 14.5, "rating": 4.9},

            # ==========================================================
            # 24. BANGALORE -> MUMBAI  (~980 km, 15-17h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Bangalore", "destination": "Mumbai",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 880.00,
             "facilities": "Charging Point, Reading Light, Emergency Hammer", "dep_hour": 15, "dep_min": 30, "duration_hours": 16, "rating": 4.0},
            {"operator_name": "Paulo Travels", "source": "Bangalore", "destination": "Mumbai",
             "bus_type": "AC Seater (2+2)", "price": 1050.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 16, "dep_min": 30, "duration_hours": 15, "rating": 4.3},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Mumbai",
             "bus_type": "AC Sleeper (2+1)", "price": 1399.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, CCTV", "dep_hour": 17, "dep_min": 30, "duration_hours": 15, "rating": 4.6},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Mumbai",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1799.00,
             "facilities": "WiFi, Luxury Pillows, Blankets, GPS, Air Suspension", "dep_hour": 18, "dep_min": 0, "duration_hours": 14.5, "rating": 4.9},

            # ==========================================================
            # 25. MUMBAI -> HYDERABAD  (~710 km, 12-14h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Mumbai", "destination": "Hyderabad",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 750.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 17, "dep_min": 0, "duration_hours": 13, "rating": 4.0},
            {"operator_name": "National Travels", "source": "Mumbai", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 899.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 18, "dep_min": 0, "duration_hours": 12.5, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Mumbai", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 1199.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, GPS", "dep_hour": 19, "dep_min": 0, "duration_hours": 12, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Mumbai", "destination": "Hyderabad",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1550.00,
             "facilities": "WiFi, Luxury Pillows, Blankets, GPS, Air Suspension", "dep_hour": 19, "dep_min": 30, "duration_hours": 12, "rating": 4.9},

            # ==========================================================
            # 26. HYDERABAD -> MUMBAI  (~710 km, 12-14h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Hyderabad", "destination": "Mumbai",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 780.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 16, "dep_min": 30, "duration_hours": 13, "rating": 4.0},
            {"operator_name": "National Travels", "source": "Hyderabad", "destination": "Mumbai",
             "bus_type": "AC Seater (2+2)", "price": 920.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 17, "dep_min": 30, "duration_hours": 12.5, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Hyderabad", "destination": "Mumbai",
             "bus_type": "AC Sleeper (2+1)", "price": 1220.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, GPS", "dep_hour": 18, "dep_min": 30, "duration_hours": 12, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Hyderabad", "destination": "Mumbai",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1580.00,
             "facilities": "WiFi, Luxury Pillows, Blankets, GPS, Air Suspension", "dep_hour": 19, "dep_min": 0, "duration_hours": 12, "rating": 4.9},

            # ==========================================================
            # 27. CHENNAI -> MADURAI  (~460 km, 7-8h)
            # ==========================================================
            {"operator_name": "Parveen Travels", "source": "Chennai", "destination": "Madurai",
             "bus_type": "Non-AC Seater (2+2)", "price": 380.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 8, "dep_min": 0, "duration_hours": 8, "rating": 3.9},
            {"operator_name": "KPN Travels", "source": "Chennai", "destination": "Madurai",
             "bus_type": "AC Seater (2+2)", "price": 550.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 14, "dep_min": 0, "duration_hours": 7.5, "rating": 4.4},
            {"operator_name": "SRS Travels", "source": "Chennai", "destination": "Madurai",
             "bus_type": "AC Sleeper (2+1)", "price": 799.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 21, "dep_min": 30, "duration_hours": 7, "rating": 4.6},
            {"operator_name": "Greenline Travels", "source": "Chennai", "destination": "Madurai",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 999.00,
             "facilities": "WiFi, Luxury Bedding, USB Charging, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 7, "rating": 4.8},

            # ==========================================================
            # 28. MADURAI -> CHENNAI  (~460 km, 7-8h)
            # ==========================================================
            {"operator_name": "Parveen Travels", "source": "Madurai", "destination": "Chennai",
             "bus_type": "Non-AC Seater (2+2)", "price": 390.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 7, "dep_min": 30, "duration_hours": 8, "rating": 3.9},
            {"operator_name": "KPN Travels", "source": "Madurai", "destination": "Chennai",
             "bus_type": "AC Seater (2+2)", "price": 570.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 13, "dep_min": 30, "duration_hours": 7.5, "rating": 4.4},
            {"operator_name": "SRS Travels", "source": "Madurai", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 820.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 21, "dep_min": 0, "duration_hours": 7, "rating": 4.6},
            {"operator_name": "Greenline Travels", "source": "Madurai", "destination": "Chennai",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1020.00,
             "facilities": "WiFi, Luxury Bedding, USB Charging, GPS", "dep_hour": 21, "dep_min": 30, "duration_hours": 7, "rating": 4.8},

            # ==========================================================
            # 29. CHENNAI -> COIMBATORE  (~510 km, 8-9h)
            # ==========================================================
            {"operator_name": "Parveen Travels", "source": "Chennai", "destination": "Coimbatore",
             "bus_type": "Non-AC Seater (2+2)", "price": 420.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 8, "dep_min": 30, "duration_hours": 9, "rating": 3.9},
            {"operator_name": "KPN Travels", "source": "Chennai", "destination": "Coimbatore",
             "bus_type": "AC Seater (2+2)", "price": 599.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 22, "dep_min": 0, "duration_hours": 8, "rating": 4.4},
            {"operator_name": "SRS Travels", "source": "Chennai", "destination": "Coimbatore",
             "bus_type": "AC Sleeper (2+1)", "price": 850.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 30, "duration_hours": 8, "rating": 4.6},
            {"operator_name": "Greenline Travels", "source": "Chennai", "destination": "Coimbatore",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1050.00,
             "facilities": "WiFi, Luxury Bedding, USB Charging, GPS", "dep_hour": 21, "dep_min": 15, "duration_hours": 8, "rating": 4.8},

            # ==========================================================
            # 30. COIMBATORE -> CHENNAI  (~510 km, 8-9h)
            # ==========================================================
            {"operator_name": "Parveen Travels", "source": "Coimbatore", "destination": "Chennai",
             "bus_type": "Non-AC Seater (2+2)", "price": 440.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 8, "dep_min": 0, "duration_hours": 9, "rating": 3.9},
            {"operator_name": "KPN Travels", "source": "Coimbatore", "destination": "Chennai",
             "bus_type": "AC Seater (2+2)", "price": 620.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 21, "dep_min": 30, "duration_hours": 8, "rating": 4.4},
            {"operator_name": "SRS Travels", "source": "Coimbatore", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 870.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 0, "duration_hours": 8, "rating": 4.6},
            {"operator_name": "Greenline Travels", "source": "Coimbatore", "destination": "Chennai",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1080.00,
             "facilities": "WiFi, Luxury Bedding, USB Charging, GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 8, "rating": 4.8},

            # ==========================================================
            # 31. BANGALORE -> MYSORE  (~150 km, 3-3.5h)
            # ==========================================================
            {"operator_name": "KSRTC Airavat", "source": "Bangalore", "destination": "Mysore",
             "bus_type": "Non-AC Seater (2+2)", "price": 150.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 0, "duration_hours": 3.5, "rating": 4.0},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Mysore",
             "bus_type": "AC Seater (2+2)", "price": 280.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 8, "dep_min": 0, "duration_hours": 3, "rating": 4.4},
            {"operator_name": "IntrCity SmartBus", "source": "Bangalore", "destination": "Mysore",
             "bus_type": "AC Seater (2+2)", "price": 350.00,
             "facilities": "WiFi, Lounge Access, USB Charging, Water Bottle", "dep_hour": 10, "dep_min": 0, "duration_hours": 3, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Mysore",
             "bus_type": "AC Sleeper (2+1)", "price": 450.00,
             "facilities": "WiFi, Blankets, Charging Point, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 3, "rating": 4.8},

            # ==========================================================
            # 32. MYSORE -> BANGALORE  (~150 km, 3-3.5h)
            # ==========================================================
            {"operator_name": "KSRTC Airavat", "source": "Mysore", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 160.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 30, "duration_hours": 3.5, "rating": 4.0},
            {"operator_name": "SRS Travels", "source": "Mysore", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 290.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 9, "dep_min": 0, "duration_hours": 3, "rating": 4.4},
            {"operator_name": "IntrCity SmartBus", "source": "Mysore", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 360.00,
             "facilities": "WiFi, Lounge Access, USB Charging, Water Bottle", "dep_hour": 14, "dep_min": 0, "duration_hours": 3, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Mysore", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 470.00,
             "facilities": "WiFi, Blankets, Charging Point, GPS", "dep_hour": 21, "dep_min": 30, "duration_hours": 3, "rating": 4.8},

            # ==========================================================
            # 33. BANGALORE -> MANGALORE  (~350 km, 7-8h)
            # ==========================================================
            {"operator_name": "KSRTC Airavat", "source": "Bangalore", "destination": "Mangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 380.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 8, "dep_min": 0, "duration_hours": 8, "rating": 3.9},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Mangalore",
             "bus_type": "AC Seater (2+2)", "price": 550.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 14, "dep_min": 0, "duration_hours": 7.5, "rating": 4.3},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Mangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 850.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 0, "duration_hours": 7, "rating": 4.7},
            {"operator_name": "Orange Travels", "source": "Bangalore", "destination": "Mangalore",
             "bus_type": "Multi-Axle AC Sleeper (2+1)", "price": 1050.00,
             "facilities": "WiFi, Luxury Bedding, GPS, Air Suspension", "dep_hour": 22, "dep_min": 30, "duration_hours": 7, "rating": 4.8},

            # ==========================================================
            # 34. MANGALORE -> BANGALORE  (~350 km, 7-8h)
            # ==========================================================
            {"operator_name": "KSRTC Airavat", "source": "Mangalore", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 390.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 7, "dep_min": 30, "duration_hours": 8, "rating": 3.9},
            {"operator_name": "SRS Travels", "source": "Mangalore", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 570.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 13, "dep_min": 30, "duration_hours": 7.5, "rating": 4.3},
            {"operator_name": "VRL Travels", "source": "Mangalore", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 870.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 21, "dep_min": 30, "duration_hours": 7, "rating": 4.7},
            {"operator_name": "Orange Travels", "source": "Mangalore", "destination": "Bangalore",
             "bus_type": "Multi-Axle AC Sleeper (2+1)", "price": 1080.00,
             "facilities": "WiFi, Luxury Bedding, GPS, Air Suspension", "dep_hour": 22, "dep_min": 0, "duration_hours": 7, "rating": 4.8},

            # ==========================================================
            # 35. DELHI -> LUCKNOW  (~550 km, 8-10h)
            # ==========================================================
            {"operator_name": "UPSRTC Volvo", "source": "Delhi", "destination": "Lucknow",
             "bus_type": "Non-AC Seater (2+2)", "price": 450.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 7, "dep_min": 0, "duration_hours": 9.5, "rating": 3.9},
            {"operator_name": "Zingbus", "source": "Delhi", "destination": "Lucknow",
             "bus_type": "AC Seater (2+2)", "price": 650.00,
             "facilities": "WiFi, USB Charging, Reclining Seats, Live Tracking", "dep_hour": 22, "dep_min": 0, "duration_hours": 8.5, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Delhi", "destination": "Lucknow",
             "bus_type": "AC Sleeper (2+1)", "price": 899.00,
             "facilities": "WiFi, Lounge, Blankets, USB Charging, GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 8, "rating": 4.7},
            {"operator_name": "Goldline Super Deluxe", "source": "Delhi", "destination": "Lucknow",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1150.00,
             "facilities": "WiFi, Luxury Bedding, Mineral Water, GPS", "dep_hour": 23, "dep_min": 0, "duration_hours": 8, "rating": 4.8},

            # ==========================================================
            # 36. LUCKNOW -> DELHI  (~550 km, 8-10h)
            # ==========================================================
            {"operator_name": "UPSRTC Volvo", "source": "Lucknow", "destination": "Delhi",
             "bus_type": "Non-AC Seater (2+2)", "price": 470.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 30, "duration_hours": 9.5, "rating": 3.9},
            {"operator_name": "Zingbus", "source": "Lucknow", "destination": "Delhi",
             "bus_type": "AC Seater (2+2)", "price": 680.00,
             "facilities": "WiFi, USB Charging, Reclining Seats, Live Tracking", "dep_hour": 21, "dep_min": 30, "duration_hours": 8.5, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Lucknow", "destination": "Delhi",
             "bus_type": "AC Sleeper (2+1)", "price": 920.00,
             "facilities": "WiFi, Lounge, Blankets, USB Charging, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 8, "rating": 4.7},
            {"operator_name": "Goldline Super Deluxe", "source": "Lucknow", "destination": "Delhi",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1180.00,
             "facilities": "WiFi, Luxury Bedding, Mineral Water, GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 8, "rating": 4.8},

            # ==========================================================
            # 37. HYDERABAD -> TIRUPATI  (~550 km, 9-10h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda", "source": "Hyderabad", "destination": "Tirupati",
             "bus_type": "Non-AC Seater (2+2)", "price": 480.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 18, "dep_min": 0, "duration_hours": 10, "rating": 3.9},
            {"operator_name": "SRE Travels", "source": "Hyderabad", "destination": "Tirupati",
             "bus_type": "AC Seater (2+2)", "price": 699.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 19, "dep_min": 0, "duration_hours": 9.5, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Hyderabad", "destination": "Tirupati",
             "bus_type": "AC Sleeper (2+1)", "price": 950.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, GPS", "dep_hour": 21, "dep_min": 0, "duration_hours": 9, "rating": 4.7},
            {"operator_name": "Kaveri Travels", "source": "Hyderabad", "destination": "Tirupati",
             "bus_type": "Multi-Axle AC Sleeper (2+1)", "price": 1199.00,
             "facilities": "WiFi, Luxury Bedding, GPS, Air Suspension", "dep_hour": 22, "dep_min": 0, "duration_hours": 9, "rating": 4.8},

            # ==========================================================
            # 38. TIRUPATI -> HYDERABAD  (~550 km, 9-10h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda", "source": "Tirupati", "destination": "Hyderabad",
             "bus_type": "Non-AC Seater (2+2)", "price": 499.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 17, "dep_min": 30, "duration_hours": 10, "rating": 3.9},
            {"operator_name": "SRE Travels", "source": "Tirupati", "destination": "Hyderabad",
             "bus_type": "AC Seater (2+2)", "price": 720.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 18, "dep_min": 30, "duration_hours": 9.5, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Tirupati", "destination": "Hyderabad",
             "bus_type": "AC Sleeper (2+1)", "price": 980.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, GPS", "dep_hour": 20, "dep_min": 30, "duration_hours": 9, "rating": 4.7},
            {"operator_name": "Kaveri Travels", "source": "Tirupati", "destination": "Hyderabad",
             "bus_type": "Multi-Axle AC Sleeper (2+1)", "price": 1220.00,
             "facilities": "WiFi, Luxury Bedding, GPS, Air Suspension", "dep_hour": 21, "dep_min": 30, "duration_hours": 9, "rating": 4.8},

            # ==========================================================
            # 39. CHENNAI -> TIRUPATI  (~135 km, 3-3.5h)
            # ==========================================================
            {"operator_name": "APSRTC Express", "source": "Chennai", "destination": "Tirupati",
             "bus_type": "Non-AC Seater (2+2)", "price": 180.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 5, "dep_min": 30, "duration_hours": 3.5, "rating": 3.9},
            {"operator_name": "SRE Travels", "source": "Chennai", "destination": "Tirupati",
             "bus_type": "AC Seater (2+2)", "price": 320.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 7, "dep_min": 0, "duration_hours": 3, "rating": 4.4},
            {"operator_name": "KPN Travels", "source": "Chennai", "destination": "Tirupati",
             "bus_type": "AC Sleeper (2+1)", "price": 450.00,
             "facilities": "WiFi, Blankets, Charging Point", "dep_hour": 22, "dep_min": 0, "duration_hours": 3, "rating": 4.6},

            # ==========================================================
            # 40. TIRUPATI -> CHENNAI  (~135 km, 3-3.5h)
            # ==========================================================
            {"operator_name": "APSRTC Express", "source": "Tirupati", "destination": "Chennai",
             "bus_type": "Non-AC Seater (2+2)", "price": 190.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 0, "duration_hours": 3.5, "rating": 3.9},
            {"operator_name": "SRE Travels", "source": "Tirupati", "destination": "Chennai",
             "bus_type": "AC Seater (2+2)", "price": 330.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 8, "dep_min": 0, "duration_hours": 3, "rating": 4.4},
            {"operator_name": "KPN Travels", "source": "Tirupati", "destination": "Chennai",
             "bus_type": "AC Sleeper (2+1)", "price": 470.00,
             "facilities": "WiFi, Blankets, Charging Point", "dep_hour": 21, "dep_min": 30, "duration_hours": 3, "rating": 4.6},

            # ==========================================================
            # 41. MUMBAI -> SHIRDI  (~250 km, 5-6h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Mumbai", "destination": "Shirdi",
             "bus_type": "Non-AC Seater (2+2)", "price": 280.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 5, "dep_min": 30, "duration_hours": 6, "rating": 3.9},
            {"operator_name": "Shrinath Travels", "source": "Mumbai", "destination": "Shirdi",
             "bus_type": "AC Seater (2+2)", "price": 420.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 6, "dep_min": 30, "duration_hours": 5.5, "rating": 4.4},
            {"operator_name": "Neeta Tours & Travels", "source": "Mumbai", "destination": "Shirdi",
             "bus_type": "AC Sleeper (2+1)", "price": 599.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 0, "duration_hours": 5, "rating": 4.6},

            # ==========================================================
            # 42. SHIRDI -> MUMBAI  (~250 km, 5-6h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Shirdi", "destination": "Mumbai",
             "bus_type": "Non-AC Seater (2+2)", "price": 290.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 6, "dep_min": 0, "duration_hours": 6, "rating": 3.9},
            {"operator_name": "Shrinath Travels", "source": "Shirdi", "destination": "Mumbai",
             "bus_type": "AC Seater (2+2)", "price": 440.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 14, "dep_min": 0, "duration_hours": 5.5, "rating": 4.4},
            {"operator_name": "Neeta Tours & Travels", "source": "Shirdi", "destination": "Mumbai",
             "bus_type": "AC Sleeper (2+1)", "price": 620.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 17, "dep_min": 0, "duration_hours": 5, "rating": 4.6},

            # ==========================================================
            # 43. PUNE -> BANGALORE  (~840 km, 13-15h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Pune", "destination": "Bangalore",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 750.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 17, "dep_min": 0, "duration_hours": 14, "rating": 4.0},
            {"operator_name": "National Travels", "source": "Pune", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 950.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 18, "dep_min": 0, "duration_hours": 13.5, "rating": 4.3},
            {"operator_name": "SRS Travels", "source": "Pune", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 1250.00,
             "facilities": "WiFi, Blankets, Charging Point, CCTV", "dep_hour": 19, "dep_min": 0, "duration_hours": 13, "rating": 4.6},
            {"operator_name": "VRL Travels", "source": "Pune", "destination": "Bangalore",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1599.00,
             "facilities": "WiFi, Luxury Pillows, Blankets, GPS, Air Suspension", "dep_hour": 19, "dep_min": 30, "duration_hours": 13, "rating": 4.9},

            # ==========================================================
            # 44. BANGALORE -> PUNE  (~840 km, 13-15h)
            # ==========================================================
            {"operator_name": "Sharma Travels", "source": "Bangalore", "destination": "Pune",
             "bus_type": "Non-AC Sleeper (2+1)", "price": 780.00,
             "facilities": "Charging Point, Reading Light", "dep_hour": 16, "dep_min": 30, "duration_hours": 14, "rating": 4.0},
            {"operator_name": "National Travels", "source": "Bangalore", "destination": "Pune",
             "bus_type": "AC Seater (2+2)", "price": 980.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 17, "dep_min": 30, "duration_hours": 13.5, "rating": 4.3},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Pune",
             "bus_type": "AC Sleeper (2+1)", "price": 1280.00,
             "facilities": "WiFi, Blankets, Charging Point, CCTV", "dep_hour": 18, "dep_min": 30, "duration_hours": 13, "rating": 4.6},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Pune",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1650.00,
             "facilities": "WiFi, Luxury Pillows, Blankets, GPS, Air Suspension", "dep_hour": 19, "dep_min": 0, "duration_hours": 13, "rating": 4.9},

            # ==========================================================
            # 45. PUNE -> GOA  (~450 km, 8-10h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Pune", "destination": "Goa",
             "bus_type": "Non-AC Seater (2+2)", "price": 550.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 18, "dep_min": 0, "duration_hours": 9, "rating": 3.9},
            {"operator_name": "Paulo Travels", "source": "Pune", "destination": "Goa",
             "bus_type": "AC Seater (2+2)", "price": 750.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 19, "dep_min": 0, "duration_hours": 8.5, "rating": 4.4},
            {"operator_name": "Neeta Tours & Travels", "source": "Pune", "destination": "Goa",
             "bus_type": "AC Sleeper (2+1)", "price": 999.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 21, "dep_min": 0, "duration_hours": 8, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Pune", "destination": "Goa",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1350.00,
             "facilities": "WiFi, Luxury Pillows, GPS, Air Suspension", "dep_hour": 22, "dep_min": 0, "duration_hours": 8, "rating": 4.9},

            # ==========================================================
            # 46. GOA -> PUNE  (~450 km, 8-10h)
            # ==========================================================
            {"operator_name": "Mahalaxmi Travels", "source": "Goa", "destination": "Pune",
             "bus_type": "Non-AC Seater (2+2)", "price": 570.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 17, "dep_min": 30, "duration_hours": 9, "rating": 3.9},
            {"operator_name": "Paulo Travels", "source": "Goa", "destination": "Pune",
             "bus_type": "AC Seater (2+2)", "price": 780.00,
             "facilities": "AC, Reclining Seats, USB Charging, Water Bottle", "dep_hour": 18, "dep_min": 30, "duration_hours": 8.5, "rating": 4.4},
            {"operator_name": "Neeta Tours & Travels", "source": "Goa", "destination": "Pune",
             "bus_type": "AC Sleeper (2+1)", "price": 1020.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 20, "dep_min": 30, "duration_hours": 8, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Goa", "destination": "Pune",
             "bus_type": "Multi-Axle Volvo AC Sleeper (2+1)", "price": 1380.00,
             "facilities": "WiFi, Luxury Pillows, GPS, Air Suspension", "dep_hour": 21, "dep_min": 30, "duration_hours": 8, "rating": 4.9},

            # ==========================================================
            # 47. VIJAYAWADA -> BANGALORE  (~660 km, 10-12h)
            # ==========================================================
            {"operator_name": "APSRTC Garuda", "source": "Vijayawada", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 580.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 17, "dep_min": 0, "duration_hours": 11.5, "rating": 3.9},
            {"operator_name": "Sri Krishna Travels", "source": "Vijayawada", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 799.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 18, "dep_min": 30, "duration_hours": 11, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Vijayawada", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 1099.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, GPS", "dep_hour": 20, "dep_min": 0, "duration_hours": 10.5, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Vijayawada", "destination": "Bangalore",
             "bus_type": "Multi-Axle AC Sleeper (2+1)", "price": 1399.00,
             "facilities": "WiFi, Luxury Pillows, GPS, Air Suspension", "dep_hour": 21, "dep_min": 0, "duration_hours": 10, "rating": 4.9},

            # ==========================================================
            # 48. BANGALORE -> VIJAYAWADA  (~660 km, 10-12h)
            # ==========================================================
            {"operator_name": "KSRTC Flybus", "source": "Bangalore", "destination": "Vijayawada",
             "bus_type": "Non-AC Seater (2+2)", "price": 599.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 17, "dep_min": 30, "duration_hours": 11.5, "rating": 3.9},
            {"operator_name": "Sri Krishna Travels", "source": "Bangalore", "destination": "Vijayawada",
             "bus_type": "AC Seater (2+2)", "price": 820.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 19, "dep_min": 0, "duration_hours": 11, "rating": 4.3},
            {"operator_name": "Orange Travels", "source": "Bangalore", "destination": "Vijayawada",
             "bus_type": "AC Sleeper (2+1)", "price": 1120.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle, GPS", "dep_hour": 20, "dep_min": 30, "duration_hours": 10.5, "rating": 4.7},
            {"operator_name": "VRL Travels", "source": "Bangalore", "destination": "Vijayawada",
             "bus_type": "Multi-Axle AC Sleeper (2+1)", "price": 1450.00,
             "facilities": "WiFi, Luxury Pillows, GPS, Air Suspension", "dep_hour": 21, "dep_min": 30, "duration_hours": 10, "rating": 4.9},

            # ==========================================================
            # 49. BANGALORE -> COIMBATORE  (~370 km, 6-7.5h)
            # ==========================================================
            {"operator_name": "KSRTC Airavat", "source": "Bangalore", "destination": "Coimbatore",
             "bus_type": "Non-AC Seater (2+2)", "price": 350.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 7, "dep_min": 30, "duration_hours": 7.5, "rating": 3.9},
            {"operator_name": "SRS Travels", "source": "Bangalore", "destination": "Coimbatore",
             "bus_type": "AC Seater (2+2)", "price": 520.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 14, "dep_min": 0, "duration_hours": 7, "rating": 4.3},
            {"operator_name": "KPN Travels", "source": "Bangalore", "destination": "Coimbatore",
             "bus_type": "AC Sleeper (2+1)", "price": 799.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 22, "dep_min": 0, "duration_hours": 6.5, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Bangalore", "destination": "Coimbatore",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 999.00,
             "facilities": "WiFi, Lounge, Luxury Bedding, GPS", "dep_hour": 22, "dep_min": 30, "duration_hours": 6, "rating": 4.8},

            # ==========================================================
            # 50. COIMBATORE -> BANGALORE  (~370 km, 6-7.5h)
            # ==========================================================
            {"operator_name": "KSRTC Airavat", "source": "Coimbatore", "destination": "Bangalore",
             "bus_type": "Non-AC Seater (2+2)", "price": 360.00,
             "facilities": "Fan, Reclining Seats", "dep_hour": 7, "dep_min": 0, "duration_hours": 7.5, "rating": 3.9},
            {"operator_name": "SRS Travels", "source": "Coimbatore", "destination": "Bangalore",
             "bus_type": "AC Seater (2+2)", "price": 540.00,
             "facilities": "AC, USB Charging, Water Bottle", "dep_hour": 13, "dep_min": 30, "duration_hours": 7, "rating": 4.3},
            {"operator_name": "KPN Travels", "source": "Coimbatore", "destination": "Bangalore",
             "bus_type": "AC Sleeper (2+1)", "price": 820.00,
             "facilities": "WiFi, Blankets, Charging Point, Water Bottle", "dep_hour": 21, "dep_min": 30, "duration_hours": 6.5, "rating": 4.6},
            {"operator_name": "IntrCity SmartBus", "source": "Coimbatore", "destination": "Bangalore",
             "bus_type": "Scania AC Sleeper (2+1)", "price": 1020.00,
             "facilities": "WiFi, Lounge, Luxury Bedding, GPS", "dep_hour": 22, "dep_min": 0, "duration_hours": 6, "rating": 4.8},
        ]

        print(f"[*] Compiling fleet across {len(routes_catalog)} route templates for the next 30 days...")
        now = datetime.now()
        bus_rows = []

        for day_offset in range(0, 30):
            trip_date = now.date() + timedelta(days=day_offset)
            for t in routes_catalog:
                dep_dt = datetime(trip_date.year, trip_date.month, trip_date.day, t["dep_hour"], t["dep_min"])
                arr_dt = dep_dt + timedelta(hours=t["duration_hours"])
                bus_rows.append((
                    t["operator_name"],
                    t["source"],
                    t["destination"],
                    dep_dt.strftime("%Y-%m-%d %H:%M"),
                    arr_dt.strftime("%Y-%m-%d %H:%M"),
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, bus_rows)

        print(f"[+] Successfully seeded {len(bus_rows)} active bus schedules across 30 travel days!")

        # Pre-seed sample reservations for lower and upper deck
        cursor.execute("SELECT bus_id, bus_type FROM buses LIMIT 100;")
        sample_buses = cursor.fetchall()
        reservations = []
        for b in sample_buses:
            b_id = b['bus_id']
            reservations.extend([
                (b_id, "L2", "lower", "sleeper", 1, 1),  # ladies booked
                (b_id, "L5", "lower", "sleeper", 1, 0),  # booked
                (b_id, "U3", "upper", "sleeper", 1, 0),  # booked
                (b_id, "U8", "upper", "sleeper", 1, 1),  # ladies booked
            ])
        cursor.executemany("""
            INSERT IGNORE INTO seat_reservations 
            (bus_id, seat_number, deck, seat_type, is_booked, is_ladies)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, reservations)
        print(f"[+] Populated seat reservations across {len(sample_buses)} active buses.")

    conn.close()

if __name__ == "__main__":
    seed_all_buses()
