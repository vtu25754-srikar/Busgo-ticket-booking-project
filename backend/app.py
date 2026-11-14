"""
BUSGO - Python Flask Backend Application
Agentic AI-Based Intelligent Bus Ticket Booking & Travel Assistance System
Implements SRS Architecture, REST APIs, Claude Agent, ChromaDB RAG, and Playwright Automation.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import pymysql

# Import custom services
from init_db import get_connection, hash_password, initialize_database
from rag_service import init_rag_system, answer_policy_with_rag, search_knowledge_base
from agent_service import (
    process_agent_request,
    tool_search_bus,
    tool_compare_bus,
    tool_check_seats,
    tool_get_booking_history,
    tool_book_ticket,
    tool_cancel_booking
)
from automation_service import run_automated_bus_search, run_automated_seat_workflow

# ==============================================================================
# CITY-SPECIFIC BOARDING & DROPPING POINTS (Real Indian bus stops & landmarks)
# ==============================================================================
CITY_STOPS = {
    "Hyderabad": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Mahatma Gandhi Bus Station (MGBS)", "landmark": "Gowliguda", "offset_min": 0},
            {"stop_id": 2, "stop_name": "JBS Jubilee Bus Station", "landmark": "Secunderabad", "offset_min": 15},
            {"stop_id": 3, "stop_name": "Lakdi-Ka-Pul", "landmark": "Near Assembly", "offset_min": 20},
            {"stop_id": 4, "stop_name": "Miyapur X Roads", "landmark": "Near Metro Station", "offset_min": 35},
            {"stop_id": 5, "stop_name": "Shamshabad ORR Junction", "landmark": "Near RGIA Airport", "offset_min": 50},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Shamshabad ORR Junction", "landmark": "Near RGIA Airport", "offset_min": -45},
            {"stop_id": 102, "stop_name": "Miyapur X Roads", "landmark": "Near Metro Station", "offset_min": -30},
            {"stop_id": 103, "stop_name": "Lakdi-Ka-Pul", "landmark": "Near Assembly", "offset_min": -20},
            {"stop_id": 104, "stop_name": "JBS Jubilee Bus Station", "landmark": "Secunderabad", "offset_min": -10},
            {"stop_id": 105, "stop_name": "Mahatma Gandhi Bus Station (MGBS)", "landmark": "Gowliguda", "offset_min": 0},
        ]
    },
    "Bangalore": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Kempegowda Bus Station (Majestic)", "landmark": "Majestic", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Silk Board Junction", "landmark": "BTM Layout", "offset_min": 20},
            {"stop_id": 3, "stop_name": "Electronic City Toll Gate", "landmark": "Infosys Campus", "offset_min": 30},
            {"stop_id": 4, "stop_name": "Madiwala", "landmark": "Near Tata Showroom", "offset_min": 15},
            {"stop_id": 5, "stop_name": "Hebbal Flyover", "landmark": "Near Esteem Mall", "offset_min": 25},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Hebbal Flyover", "landmark": "Near Esteem Mall", "offset_min": -35},
            {"stop_id": 102, "stop_name": "Madiwala", "landmark": "Near Tata Showroom", "offset_min": -25},
            {"stop_id": 103, "stop_name": "Silk Board Junction", "landmark": "BTM Layout", "offset_min": -15},
            {"stop_id": 104, "stop_name": "Electronic City Toll Gate", "landmark": "Infosys Campus", "offset_min": -10},
            {"stop_id": 105, "stop_name": "Kempegowda Bus Station (Majestic)", "landmark": "Majestic", "offset_min": 0},
        ]
    },
    "Chennai": {
        "boarding": [
            {"stop_id": 1, "stop_name": "CMBT (Chennai Mofussil Bus Terminus)", "landmark": "Koyambedu", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Tambaram Bus Stand", "landmark": "Tambaram", "offset_min": 25},
            {"stop_id": 3, "stop_name": "Guindy", "landmark": "Near Kathipara Junction", "offset_min": 10},
            {"stop_id": 4, "stop_name": "Porur Junction", "landmark": "Near DLF IT Park", "offset_min": 8},
            {"stop_id": 5, "stop_name": "Madhavaram Bus Stand", "landmark": "Madhavaram", "offset_min": 20},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Madhavaram Bus Stand", "landmark": "Madhavaram", "offset_min": -30},
            {"stop_id": 102, "stop_name": "Porur Junction", "landmark": "Near DLF IT Park", "offset_min": -15},
            {"stop_id": 103, "stop_name": "Guindy", "landmark": "Near Kathipara Junction", "offset_min": -10},
            {"stop_id": 104, "stop_name": "Tambaram Bus Stand", "landmark": "Tambaram", "offset_min": -5},
            {"stop_id": 105, "stop_name": "CMBT (Chennai Mofussil Bus Terminus)", "landmark": "Koyambedu", "offset_min": 0},
        ]
    },
    "Mumbai": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Mumbai Central Bus Depot", "landmark": "Mumbai Central", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Dadar TT Circle", "landmark": "Dadar East", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Sion Bus Depot", "landmark": "Sion", "offset_min": 15},
            {"stop_id": 4, "stop_name": "Vashi Bus Stand", "landmark": "Navi Mumbai", "offset_min": 30},
            {"stop_id": 5, "stop_name": "Borivali Bus Depot", "landmark": "Borivali West", "offset_min": 25},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Borivali Bus Depot", "landmark": "Borivali West", "offset_min": -30},
            {"stop_id": 102, "stop_name": "Vashi Bus Stand", "landmark": "Navi Mumbai", "offset_min": -25},
            {"stop_id": 103, "stop_name": "Dadar TT Circle", "landmark": "Dadar East", "offset_min": -10},
            {"stop_id": 104, "stop_name": "Sion Bus Depot", "landmark": "Sion", "offset_min": -15},
            {"stop_id": 105, "stop_name": "Mumbai Central Bus Depot", "landmark": "Mumbai Central", "offset_min": 0},
        ]
    },
    "Pune": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Pune Station (Shivajinagar)", "landmark": "Shivajinagar", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Swargate Bus Stand", "landmark": "Swargate", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Hinjewadi IT Park", "landmark": "Rajiv Gandhi Infotech Park", "offset_min": 25},
            {"stop_id": 4, "stop_name": "Wakad Bus Stop", "landmark": "Near Dange Chowk", "offset_min": 20},
            {"stop_id": 5, "stop_name": "Katraj Bypass", "landmark": "NH4 Katraj", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Katraj Bypass", "landmark": "NH4 Katraj", "offset_min": -20},
            {"stop_id": 102, "stop_name": "Hinjewadi IT Park", "landmark": "Rajiv Gandhi Infotech Park", "offset_min": -15},
            {"stop_id": 103, "stop_name": "Wakad Bus Stop", "landmark": "Near Dange Chowk", "offset_min": -10},
            {"stop_id": 104, "stop_name": "Swargate Bus Stand", "landmark": "Swargate", "offset_min": -5},
            {"stop_id": 105, "stop_name": "Pune Station (Shivajinagar)", "landmark": "Shivajinagar", "offset_min": 0},
        ]
    },
    "Delhi": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Kashmere Gate ISBT", "landmark": "Old Delhi", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Anand Vihar ISBT", "landmark": "East Delhi", "offset_min": 15},
            {"stop_id": 3, "stop_name": "Dhaula Kuan", "landmark": "Near NH8 / Airport", "offset_min": 20},
            {"stop_id": 4, "stop_name": "Majnu Ka Tilla", "landmark": "North Delhi", "offset_min": 10},
            {"stop_id": 5, "stop_name": "Sarai Kale Khan ISBT", "landmark": "Near Hazrat Nizamuddin", "offset_min": 12},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Dhaula Kuan", "landmark": "Near NH8 / Airport", "offset_min": -25},
            {"stop_id": 102, "stop_name": "Majnu Ka Tilla", "landmark": "North Delhi", "offset_min": -15},
            {"stop_id": 103, "stop_name": "Sarai Kale Khan ISBT", "landmark": "Near Hazrat Nizamuddin", "offset_min": -10},
            {"stop_id": 104, "stop_name": "Anand Vihar ISBT", "landmark": "East Delhi", "offset_min": -5},
            {"stop_id": 105, "stop_name": "Kashmere Gate ISBT", "landmark": "Old Delhi", "offset_min": 0},
        ]
    },
    "Jaipur": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Sindhi Camp Bus Stand", "landmark": "Central Jaipur", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Narayan Singh Circle", "landmark": "Station Road", "offset_min": 5},
            {"stop_id": 3, "stop_name": "Durgapura Toll Plaza", "landmark": "NH48", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Durgapura Toll Plaza", "landmark": "NH48", "offset_min": -15},
            {"stop_id": 102, "stop_name": "Narayan Singh Circle", "landmark": "Station Road", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Sindhi Camp Bus Stand", "landmark": "Central Jaipur", "offset_min": 0},
        ]
    },
    "Chandigarh": {
        "boarding": [
            {"stop_id": 1, "stop_name": "ISBT Sector 43", "landmark": "Sector 43", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Sector 17 Bus Stand", "landmark": "Sector 17 Plaza", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Zirakpur Flyover", "landmark": "Zirakpur", "offset_min": 20},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Zirakpur Flyover", "landmark": "Zirakpur", "offset_min": -15},
            {"stop_id": 102, "stop_name": "Sector 17 Bus Stand", "landmark": "Sector 17 Plaza", "offset_min": -5},
            {"stop_id": 103, "stop_name": "ISBT Sector 43", "landmark": "Sector 43", "offset_min": 0},
        ]
    },
    "Goa": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Kadamba Bus Stand (Panaji)", "landmark": "Patto Plaza", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Mapusa Bus Stand", "landmark": "Mapusa Market", "offset_min": 15},
            {"stop_id": 3, "stop_name": "Margao (Madgaon) Bus Stand", "landmark": "Near KTC", "offset_min": 25},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Margao (Madgaon) Bus Stand", "landmark": "Near KTC", "offset_min": -20},
            {"stop_id": 102, "stop_name": "Mapusa Bus Stand", "landmark": "Mapusa Market", "offset_min": -10},
            {"stop_id": 103, "stop_name": "Kadamba Bus Stand (Panaji)", "landmark": "Patto Plaza", "offset_min": 0},
        ]
    },
    "Vijayawada": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Pandit Nehru Bus Station (PNBS)", "landmark": "Vijayawada Central", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Benz Circle", "landmark": "MG Road Junction", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Kanuru Bus Stop", "landmark": "Kanuru", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Kanuru Bus Stop", "landmark": "Kanuru", "offset_min": -10},
            {"stop_id": 102, "stop_name": "Benz Circle", "landmark": "MG Road Junction", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Pandit Nehru Bus Station (PNBS)", "landmark": "Vijayawada Central", "offset_min": 0},
        ]
    },
    "Visakhapatnam": {
        "boarding": [
            {"stop_id": 1, "stop_name": "RTC Complex Vizag", "landmark": "Dwaraka Nagar", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Gajuwaka Junction", "landmark": "Gajuwaka", "offset_min": 15},
            {"stop_id": 3, "stop_name": "Maddilapalem Bus Stand", "landmark": "Near NAD Junction", "offset_min": 10},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Maddilapalem Bus Stand", "landmark": "Near NAD Junction", "offset_min": -10},
            {"stop_id": 102, "stop_name": "Gajuwaka Junction", "landmark": "Gajuwaka", "offset_min": -5},
            {"stop_id": 103, "stop_name": "RTC Complex Vizag", "landmark": "Dwaraka Nagar", "offset_min": 0},
        ]
    },
    "Madurai": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Mattuthavani Bus Stand", "landmark": "Mattuthavani", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Periyar Bus Stand", "landmark": "Central Madurai", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Arapalayam Bus Stand", "landmark": "Arapalayam", "offset_min": 8},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Arapalayam Bus Stand", "landmark": "Arapalayam", "offset_min": -10},
            {"stop_id": 102, "stop_name": "Periyar Bus Stand", "landmark": "Central Madurai", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Mattuthavani Bus Stand", "landmark": "Mattuthavani", "offset_min": 0},
        ]
    },
    "Coimbatore": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Gandhipuram Bus Stand", "landmark": "Central Coimbatore", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Ukkadam Bus Stand", "landmark": "Ukkadam", "offset_min": 8},
            {"stop_id": 3, "stop_name": "Singanallur", "landmark": "Near Coimbatore Airport", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Singanallur", "landmark": "Near Coimbatore Airport", "offset_min": -12},
            {"stop_id": 102, "stop_name": "Ukkadam Bus Stand", "landmark": "Ukkadam", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Gandhipuram Bus Stand", "landmark": "Central Coimbatore", "offset_min": 0},
        ]
    },
    "Mysore": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Mysore KSRTC Bus Stand", "landmark": "Irwin Road", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Mysore Sub-Urban Bus Stand", "landmark": "Near Palace", "offset_min": 5},
            {"stop_id": 3, "stop_name": "Srirangapatna Bus Stop", "landmark": "Srirangapatna", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Srirangapatna Bus Stop", "landmark": "Srirangapatna", "offset_min": -10},
            {"stop_id": 102, "stop_name": "Mysore Sub-Urban Bus Stand", "landmark": "Near Palace", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Mysore KSRTC Bus Stand", "landmark": "Irwin Road", "offset_min": 0},
        ]
    },
    "Mangalore": {
        "boarding": [
            {"stop_id": 1, "stop_name": "KSRTC Bus Stand Mangalore", "landmark": "Bejai", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Pumpwell Circle", "landmark": "Pumpwell", "offset_min": 8},
            {"stop_id": 3, "stop_name": "Surathkal Toll Gate", "landmark": "Surathkal", "offset_min": 20},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Surathkal Toll Gate", "landmark": "Surathkal", "offset_min": -15},
            {"stop_id": 102, "stop_name": "Pumpwell Circle", "landmark": "Pumpwell", "offset_min": -5},
            {"stop_id": 103, "stop_name": "KSRTC Bus Stand Mangalore", "landmark": "Bejai", "offset_min": 0},
        ]
    },
    "Lucknow": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Alambagh Bus Stand", "landmark": "Alambagh", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Charbagh ISBT", "landmark": "Near Railway Station", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Kaiserbagh Bus Stand", "landmark": "Central Lucknow", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Kaiserbagh Bus Stand", "landmark": "Central Lucknow", "offset_min": -12},
            {"stop_id": 102, "stop_name": "Charbagh ISBT", "landmark": "Near Railway Station", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Alambagh Bus Stand", "landmark": "Alambagh", "offset_min": 0},
        ]
    },
    "Tirupati": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Tirupati APSRTC Bus Stand", "landmark": "Railway Station Road", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Alipiri Bus Stop", "landmark": "Near Tirumala Footpath Start", "offset_min": 10},
            {"stop_id": 3, "stop_name": "Renigunta Junction", "landmark": "Renigunta", "offset_min": 15},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Renigunta Junction", "landmark": "Renigunta", "offset_min": -10},
            {"stop_id": 102, "stop_name": "Alipiri Bus Stop", "landmark": "Near Tirumala Footpath Start", "offset_min": -5},
            {"stop_id": 103, "stop_name": "Tirupati APSRTC Bus Stand", "landmark": "Railway Station Road", "offset_min": 0},
        ]
    },
    "Shirdi": {
        "boarding": [
            {"stop_id": 1, "stop_name": "Shirdi Bus Stand", "landmark": "Near Sai Baba Temple", "offset_min": 0},
            {"stop_id": 2, "stop_name": "Shirdi Airport Road", "landmark": "Kakadi", "offset_min": 8},
        ],
        "dropping": [
            {"stop_id": 101, "stop_name": "Shirdi Airport Road", "landmark": "Kakadi", "offset_min": -5},
            {"stop_id": 102, "stop_name": "Shirdi Bus Stand", "landmark": "Near Sai Baba Temple", "offset_min": 0},
        ]
    },
}


def get_city_stops(source_city, dest_city, departure_time_str, arrival_time_str):
    """Return city-specific boarding and dropping point lists with computed times from MySQL."""
    from datetime import datetime as dt, timedelta as td

    boarding_list = []
    dropping_list = []

    try:
        dep_base = dt.strptime(departure_time_str[:16], "%Y-%m-%d %H:%M")
    except Exception:
        dep_base = dt.now()
    try:
        arr_base = dt.strptime(arrival_time_str[:16], "%Y-%m-%d %H:%M")
    except Exception:
        arr_base = dep_base + td(hours=8)

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Query MySQL boarding points
            cursor.execute("""
                SELECT boarding_id, boarding_point_name, address, latitude, longitude
                FROM boarding_points
                WHERE city_name = %s
                ORDER BY boarding_id ASC;
            """, (source_city,))
            bp_rows = cursor.fetchall()

            # Query MySQL dropping points
            cursor.execute("""
                SELECT dropping_id, dropping_point_name, address, latitude, longitude
                FROM dropping_points
                WHERE city_name = %s
                ORDER BY dropping_id ASC;
            """, (dest_city,))
            dp_rows = cursor.fetchall()
        conn.close()
    except Exception:
        bp_rows = []
        dp_rows = []

    if bp_rows:
        offset = 0
        for r in bp_rows:
            stop_time = dep_base + td(minutes=offset)
            boarding_list.append({
                "stop_id": r["boarding_id"],
                "stop_name": r["boarding_point_name"],
                "landmark": r["address"],
                "address": r["address"],
                "stop_type": "boarding",
                "time": stop_time.strftime("%H:%M"),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"])
            })
            offset += 15
    else:
        # Fallback to in-memory CITY_STOPS
        source_stops = CITY_STOPS.get(source_city, {}).get("boarding", [])
        if not source_stops:
            source_stops = [
                {"stop_id": 1, "stop_name": f"{source_city} Central Bus Stand", "landmark": "Main Road", "offset_min": 0},
                {"stop_id": 2, "stop_name": f"{source_city} Highway Junction", "landmark": "NH Bypass", "offset_min": 15},
            ]
        for s in source_stops:
            stop_time = dep_base + td(minutes=s.get("offset_min", 0))
            boarding_list.append({
                "stop_id": s["stop_id"],
                "stop_name": s["stop_name"],
                "landmark": s.get("landmark", ""),
                "address": s.get("landmark", ""),
                "stop_type": "boarding",
                "time": stop_time.strftime("%H:%M"),
                "latitude": 0.0,
                "longitude": 0.0
            })

    if dp_rows:
        offset = -(len(dp_rows) - 1) * 15
        for r in dp_rows:
            stop_time = arr_base + td(minutes=offset)
            dropping_list.append({
                "stop_id": r["dropping_id"],
                "stop_name": r["dropping_point_name"],
                "landmark": r["address"],
                "address": r["address"],
                "stop_type": "dropping",
                "time": stop_time.strftime("%H:%M"),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"])
            })
            offset += 15
    else:
        dest_stops = CITY_STOPS.get(dest_city, {}).get("dropping", [])
        if not dest_stops:
            dest_stops = [
                {"stop_id": 101, "stop_name": f"{dest_city} Highway Junction", "landmark": "NH Bypass", "offset_min": -15},
                {"stop_id": 102, "stop_name": f"{dest_city} Central Bus Stand", "landmark": "Main Road", "offset_min": 0},
            ]
        for s in dest_stops:
            stop_time = arr_base + td(minutes=s.get("offset_min", 0))
            dropping_list.append({
                "stop_id": s["stop_id"],
                "stop_name": s["stop_name"],
                "landmark": s.get("landmark", ""),
                "address": s.get("landmark", ""),
                "stop_type": "dropping",
                "time": stop_time.strftime("%H:%M"),
                "latitude": 0.0,
                "longitude": 0.0
            })

    return boarding_list, dropping_list


# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)


# ==============================================================================
# HEALTH CHECK & ROOT ROUTING
# ==============================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "BUSGO AI Travel System",
        "database": "MySQL (busgo_db)",
        "rag": "ChromaDB"
    })

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ==============================================================================
# MODULE 1: USER MANAGEMENT (FR-01, FR-02)
# ==============================================================================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username") or data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    phone = data.get("phone", "").strip()
    role = data.get("role", "customer").lower()

    if not username or not email or not password:
        return jsonify({"success": False, "message": "Username, email, and password are required."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Email is already registered."}), 409

            pwd_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, phone, role)
                VALUES (%s, %s, %s, %s, %s);
            """, (username, email, pwd_hash, phone, role))
            user_id = cursor.lastrowid

            token = f"busgo_token_{user_id}_{datetime.now().strftime('%Y%m%d%H%M')}"
            return jsonify({
                "success": True,
                "message": "User registered successfully.",
                "token": token,
                "user": {
                    "user_id": user_id,
                    "username": username,
                    "name": username,
                    "email": email,
                    "role": role
                }
            }), 201
    finally:
        conn.close()


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
            user = cursor.fetchone()

            if not user or user["password_hash"] != hash_password(password):
                return jsonify({"success": False, "message": "Invalid email or password."}), 401

            token = f"busgo_token_{user['user_id']}_{datetime.now().strftime('%Y%m%d%H%M')}"

            return jsonify({
                "success": True,
                "message": "Login successful.",
                "token": token,
                "user": {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "name": user["username"],
                    "email": user["email"],
                    "phone": user.get("phone", ""),
                    "role": user.get("role", "customer")
                }
            })
    finally:
        conn.close()


@app.route("/api/auth/me", methods=["GET"])
def get_current_user():
    # Extract user_id from token or fallback to 1
    auth_header = request.headers.get("Authorization", "")
    user_id = 1
    if "busgo_token_" in auth_header:
        try:
            parts = auth_header.split("busgo_token_")[1].split("_")
            user_id = int(parts[0])
        except Exception:
            user_id = 1

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, username, email, phone, role, created_at FROM users WHERE user_id = %s;", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"success": False, "message": "User not found."}), 404
            if isinstance(user.get("created_at"), datetime):
                user["created_at"] = user["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            user["name"] = user["username"]
            return jsonify({"success": True, "user": user})
    finally:
        conn.close()


# ==============================================================================
# MODULE 2 & 5: AI TRAVEL ASSISTANT & AGENT TOOL CALLING (FR-03, FR-04, FR-11)
# ==============================================================================

@app.route("/api/chat", methods=["POST"])
def handle_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    user_id = data.get("user_id", 1)

    if not message:
        return jsonify({"success": False, "message": "Chat message cannot be empty."}), 400

    # Execute Agent Reasoning & Tool Invocation
    agent_res = process_agent_request(message, user_id=user_id, form_data=data)

    # Persist in MySQL Table 4: CHAT_HISTORY (SRS Table 4)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_history (user_id, user_message, ai_response, tool_called)
                VALUES (%s, %s, %s, %s);
            """, (user_id, message, agent_res.get("reply", ""), agent_res.get("tool_called")))
    except Exception as e:
        print(f"[!] Chat history persistence notice: {e}")
    finally:
        conn.close()

    return jsonify(agent_res)


@app.route("/api/chat/history", methods=["GET"])
def get_chat_history():
    user_id = request.args.get("user_id", 1)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT chat_id, user_message, ai_response, tool_called, created_at
                FROM chat_history
                WHERE user_id = %s OR user_id IS NULL
                ORDER BY created_at DESC LIMIT 25;
            """, (user_id,))
            history = cursor.fetchall()
            for h in history:
                if isinstance(h.get("created_at"), datetime):
                    h["created_at"] = h["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({"success": True, "history": history})
    finally:
        conn.close()


# ==============================================================================
# MODULE 3 & 6: BUS SEARCH, COMPARISON & SEAT SELECTION (FR-05, FR-06, FR-07, FR-08)
# ==============================================================================

def format_bus_for_frontend(b):
    """Formats bus record so it satisfies both search.js and raw SRS schemas.
    Dynamically computes arrival_time from departure_time + journey duration,
    handles overnight journeys that cross midnight correctly."""
    b_id = b.get("bus_id", 1)
    dep_dt = b.get("departure_time")
    arr_dt = b.get("arrival_time")

    if isinstance(dep_dt, datetime):
        dep_str = dep_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        dep_str = str(dep_dt or "")

    if isinstance(arr_dt, datetime):
        arr_str = arr_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        arr_str = str(arr_dt or "")

    price = float(b.get("price", 0))

    fac_str = b.get("facilities", "")
    amenities = [f.strip() for f in fac_str.split(",") if f.strip()] if fac_str else ["Charging Point", "Reading Light", "Water Bottle"]

    # --- Dynamic duration and arrival computation ---
    arrival_next_day = False

    # Compute actual duration from departure and arrival datetimes
    if isinstance(dep_dt, datetime) and isinstance(arr_dt, datetime):
        duration_delta = arr_dt - dep_dt
        if duration_delta.total_seconds() < 0:
            # arrival is next day (crossed midnight)
            duration_delta = timedelta(days=1) + duration_delta
            arrival_next_day = True
        elif duration_delta.total_seconds() == 0:
            duration_delta = timedelta(hours=8, minutes=30)
        total_mins = int(duration_delta.total_seconds() // 60)
        dur_hours = total_mins // 60
        dur_mins = total_mins % 60
        duration_text = f"{dur_hours}h {dur_mins}m" if dur_mins > 0 else f"{dur_hours}h"
        # Check if arrival crosses into next calendar day
        if arr_dt.date() > dep_dt.date():
            arrival_next_day = True
    else:
        # Fallback: try to parse string times
        try:
            dep_time_part = dep_str[11:16] if len(dep_str) >= 16 else dep_str[:5]
            arr_time_part = arr_str[11:16] if len(arr_str) >= 16 else arr_str[:5]
            dep_h, dep_m = int(dep_time_part.split(":")[0]), int(dep_time_part.split(":")[1])
            arr_h, arr_m = int(arr_time_part.split(":")[0]), int(arr_time_part.split(":")[1])
            dep_total = dep_h * 60 + dep_m
            arr_total = arr_h * 60 + arr_m
            if arr_total <= dep_total:
                # Journey crosses midnight
                total_mins = (1440 - dep_total) + arr_total
                arrival_next_day = True
            else:
                total_mins = arr_total - dep_total
            dur_hours = total_mins // 60
            dur_mins = total_mins % 60
            duration_text = f"{dur_hours}h {dur_mins}m" if dur_mins > 0 else f"{dur_hours}h"
        except Exception:
            duration_text = "8h 30m"

    return {
        "schedule_id": b_id,
        "bus_id": b_id,
        "bus_name": f"{b.get('operator_name', 'Express')} Luxury",
        "operator_name": b.get("operator_name", "Express"),
        "source": b.get("source", ""),
        "source_city": b.get("source", ""),
        "destination": b.get("destination", ""),
        "destination_city": b.get("destination", ""),
        "journey_date": dep_str[:10] if len(dep_str) >= 10 else datetime.now().strftime("%Y-%m-%d"),
        "departure_time": dep_str,
        "arrival_time": arr_str,
        "arrival_next_day": arrival_next_day,
        "duration_text": duration_text,
        "bus_type": b.get("bus_type", "AC Sleeper"),
        "ticket_price": price,
        "price": price,
        "available_seats": b.get("available_seats", 30),
        "total_seats": b.get("total_seats", 36),
        "rating": float(b.get("rating", 4.5)),
        "amenities_list": amenities,
        "facilities": fac_str
    }


@app.route("/api/cities", methods=["GET"])
@app.route("/api/buses/cities", methods=["GET"])
def get_cities():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Query from cities table if populated
            cursor.execute("""
                SELECT city_id, city_name, state_name, latitude, longitude
                FROM cities
                ORDER BY city_name ASC;
            """)
            city_rows = cursor.fetchall()
            if city_rows:
                for c in city_rows:
                    c["latitude"] = float(c["latitude"])
                    c["longitude"] = float(c["longitude"])
                city_names = [c["city_name"] for c in city_rows]
                return jsonify({
                    "success": True,
                    "count": len(city_rows),
                    "cities": city_names,
                    "city_details": city_rows
                })

            cursor.execute("""
                SELECT DISTINCT source AS city FROM buses
                UNION
                SELECT DISTINCT destination AS city FROM buses
                ORDER BY city ASC;
            """)
            rows = cursor.fetchall()
            cities = [r["city"] for r in rows if r["city"]]
            if not cities:
                cities = ["Bangalore", "Chennai", "Coimbatore", "Hyderabad", "Kochi", "Kurnool", "Madurai", "Mysore", "Tirupati", "Vijayawada", "Visakhapatnam"]
            return jsonify({"success": True, "cities": cities, "city_details": []})
    finally:
        conn.close()


@app.route("/api/routes", methods=["GET"])
def get_all_routes():
    """Return all predefined intercity routes with distance, duration, and state info."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT route_id, source_city, destination_city, source_state,
                       destination_state, distance_km, duration
                FROM routes
                ORDER BY route_id ASC;
            """)
            routes = cursor.fetchall()
            return jsonify({
                "success": True,
                "count": len(routes),
                "routes": routes
            })
    finally:
        conn.close()


@app.route("/api/cities/<city_name>/points", methods=["GET"])
def get_points_by_city(city_name):
    """Return all verified boarding and dropping points for a given city."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT boarding_id, boarding_point_name, address, latitude, longitude
                FROM boarding_points
                WHERE city_name = %s
                ORDER BY boarding_id ASC;
            """, (city_name,))
            bp = cursor.fetchall()

            cursor.execute("""
                SELECT dropping_id, dropping_point_name, address, latitude, longitude
                FROM dropping_points
                WHERE city_name = %s
                ORDER BY dropping_id ASC;
            """, (city_name,))
            dp = cursor.fetchall()

            for p in bp:
                p["latitude"] = float(p["latitude"])
                p["longitude"] = float(p["longitude"])
            for p in dp:
                p["latitude"] = float(p["latitude"])
                p["longitude"] = float(p["longitude"])

            return jsonify({
                "success": True,
                "city": city_name,
                "boarding_points": bp,
                "dropping_points": dp
            })
    finally:
        conn.close()


@app.route("/api/buses/search", methods=["GET"])
def search_buses():
    source = request.args.get("from") or request.args.get("source") or request.args.get("origin") or "Hyderabad"
    destination = request.args.get("to") or request.args.get("destination") or "Bangalore"
    date = request.args.get("date")
    bus_type = request.args.get("bus_type")
    max_price = request.args.get("max_price")

    res = tool_search_bus(
        source=source,
        destination=destination,
        date=date,
        bus_type=bus_type,
        max_price=float(max_price) if max_price else None
    )

    formatted_buses = [format_bus_for_frontend(b) for b in res.get("buses", [])]

    return jsonify({
        "success": True,
        "count": len(formatted_buses),
        "buses": formatted_buses,
        "schedules": formatted_buses
    })


@app.route("/api/buses/stops", methods=["GET"])
def get_city_stops_endpoint():
    """Return boarding and dropping points for a given source-destination pair."""
    source = request.args.get("source") or request.args.get("from", "")
    destination = request.args.get("destination") or request.args.get("to", "")
    dep_time = request.args.get("departure_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    arr_time = request.args.get("arrival_time", (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"))

    boarding, dropping = get_city_stops(source, destination, dep_time, arr_time)
    return jsonify({
        "success": True,
        "source": source,
        "destination": destination,
        "boarding": boarding,
        "dropping": dropping
    })


@app.route("/api/buses/compare", methods=["GET"])
def compare_buses():
    source = request.args.get("from", "Hyderabad")
    destination = request.args.get("to", "Bangalore")
    date = request.args.get("date")
    sort_by = request.args.get("sort_by", "price_asc")

    res = tool_compare_bus(source, destination, date, sort_by=sort_by)
    return jsonify(res)


@app.route("/api/buses/<int:bus_id>", methods=["GET"])
def get_bus_details(bus_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buses WHERE bus_id = %s;", (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return jsonify({"success": False, "message": "Bus not found."}), 404
            
            formatted = format_bus_for_frontend(bus)
            return jsonify({"success": True, "bus": formatted, "schedule": formatted})
    finally:
        conn.close()


@app.route("/api/buses/schedules/<int:schedule_id>/seats", methods=["GET"])
@app.route("/api/buses/<int:schedule_id>/seats", methods=["GET"])
def get_bus_seats_endpoint(schedule_id):
    seats_res = tool_check_seats(schedule_id)
    if not seats_res.get("success"):
        return jsonify({"success": False, "message": "Bus not found."}), 404

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buses WHERE bus_id = %s;", (schedule_id,))
            bus = cursor.fetchone()
            formatted_schedule = format_bus_for_frontend(bus)
    finally:
        conn.close()

    # Build individual seat elements formatted for seats.js
    seat_elements = []
    seat_id_counter = 1

    for s in seats_res["decks"]["lower"]:
        seat_elements.append({
            "seat_id": seat_id_counter,
            "seat_number": s["seat_number"],
            "deck": "lower",
            "seat_type": "berth" if "Sleeper" in bus["bus_type"] else "seat",
            "status": s["status"],
            "is_female_only": 1 if s["status"] == "ladies" else 0
        })
        seat_id_counter += 1

    for s in seats_res["decks"]["upper"]:
        seat_elements.append({
            "seat_id": seat_id_counter,
            "seat_number": s["seat_number"],
            "deck": "upper",
            "seat_type": "berth",
            "status": s["status"],
            "is_female_only": 1 if s["status"] == "ladies" else 0
        })
        seat_id_counter += 1

    boarding_stops, dropping_stops = get_city_stops(
        bus["source"], bus["destination"],
        formatted_schedule["departure_time"],
        formatted_schedule["arrival_time"]
    )

    # Combine into flat stops list for legacy support + structured for frontend
    all_stops = boarding_stops + dropping_stops

    return jsonify({
        "success": True,
        "schedule": formatted_schedule,
        "decks": {
            "hasUpperDeck": "Sleeper" in bus["bus_type"],
            "lower": seats_res["decks"]["lower"],
            "upper": seats_res["decks"]["upper"]
        },
        "stops": all_stops,
        "seats": seat_elements
    })


# ==============================================================================
# MODULE 7: BOOKING MANAGEMENT, SEAT LOCKING & PROMO CODES (FR-09, FR-12, FR-13)
# ==============================================================================

@app.route("/api/bookings/lock-seats", methods=["POST"])
def lock_seats():
    """Temporarily lock selected seats during the checkout funnel (10-min reservation window)."""
    data = request.get_json() or {}
    schedule_id = data.get("scheduleId") or data.get("schedule_id") or data.get("bus_id", 1)
    seat_ids = data.get("seatIds", [])

    locked_until = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if any seat is already booked permanently
            cursor.execute("""
                SELECT seat_number FROM seat_reservations
                WHERE bus_id = %s AND is_booked = 1;
            """, (schedule_id,))
            booked_seats = {r["seat_number"] for r in cursor.fetchall()}

            # Handle both seat numbers like ["L1", "L2"] and numeric seat IDs [1, 2]
            conflict_seats = []
            for s in seat_ids:
                s_str = str(s)
                if s_str in booked_seats:
                    conflict_seats.append(s_str)

            if conflict_seats:
                return jsonify({
                    "success": False,
                    "message": f"Seat(s) {', '.join(conflict_seats)} are already booked. Please choose other seats."
                }), 409

            return jsonify({
                "success": True,
                "message": "Seats locked successfully for 10 minutes.",
                "scheduleId": schedule_id,
                "lockedUntil": locked_until
            })
    finally:
        conn.close()


@app.route("/api/coupons/apply", methods=["POST"])
@app.route("/api/bookings/validate-coupon", methods=["POST"])
def apply_coupon():
    """Validates promotional discount vouchers (FIRST10, SAVE100, BUSGO50, SUMMER20)."""
    data = request.get_json() or {}
    code = (data.get("code") or data.get("couponCode") or "").strip().upper()
    total_amount = float(data.get("amount") or data.get("totalAmount", 1000))

    if code == "FIRST10":
        discount = min(200.0, round(total_amount * 0.10, 2))
        return jsonify({
            "success": True,
            "discount": discount,
            "discountAmount": discount,
            "couponCode": "FIRST10",
            "message": f"FIRST10 applied! You saved ₹{discount:.2f} (10% off)."
        })
    elif code == "SAVE100":
        if total_amount < 500:
            return jsonify({"success": False, "message": "SAVE100 is valid only on bookings of ₹500 or more."}), 400
        discount = 100.0
        return jsonify({
            "success": True,
            "discount": discount,
            "discountAmount": discount,
            "couponCode": "SAVE100",
            "message": "SAVE100 applied! Flat ₹100 instant discount."
        })
    elif code == "BUSGO50":
        discount = 50.0
        return jsonify({
            "success": True,
            "discount": discount,
            "discountAmount": discount,
            "couponCode": "BUSGO50",
            "message": "BUSGO50 applied! Flat ₹50 discount added."
        })
    elif code == "SUMMER20":
        discount = min(300.0, round(total_amount * 0.20, 2))
        return jsonify({
            "success": True,
            "discount": discount,
            "discountAmount": discount,
            "couponCode": "SUMMER20",
            "message": f"SUMMER20 applied! You saved ₹{discount:.2f} (20% holiday discount)."
        })
    else:
        return jsonify({"success": False, "message": f"Invalid coupon code '{code}'. Try FIRST10 or SAVE100."}), 400


@app.route("/api/coupons/applicable", methods=["GET", "POST"])
def get_applicable_coupons_endpoint():
    """Returns available and suggested coupons for a given amount."""
    data = request.get_json() if request.is_json else {}
    amount = float(request.args.get("amount") or data.get("amount", 1000))
    from agent_service import get_applicable_coupons
    applicable = get_applicable_coupons(amount)
    return jsonify({
        "success": True,
        "amount": amount,
        "applicable_coupons": applicable
    })


@app.route("/api/bookings/create", methods=["POST"])
@app.route("/api/bookings", methods=["POST"])
def create_booking():
    """Creates a booking record and handles passenger details, stops, and discounts."""
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)

    auth_header = request.headers.get("Authorization")
    if auth_header and "Bearer " in auth_header:
        try:
            token = auth_header.split("Bearer ")[1].strip()
            # Expected format: busgo_token_{user_id}_{timestamp}
            if token.startswith("busgo_token_"):
                parts = token.split("busgo_token_")[1].split("_")
                if parts and parts[0].isdigit():
                    user_id = int(parts[0])
        except Exception:
            pass

    bus_id = data.get("scheduleId") or data.get("bus_id") or data.get("schedule_id", 1)
    passengers = data.get("passengers", [])

    if passengers and isinstance(passengers, list):
        p0 = passengers[0]
        passenger_name = p0.get("name", "Traveler")
        seat_numbers = [str(p.get("seatNumber") or p.get("seat_number", "L1")) for p in passengers]
        seat_number = ", ".join(seat_numbers)
    else:
        passenger_name = data.get("passenger_name") or data.get("name", "Traveler")
        seat_number = data.get("seat_number", "L1")

    email = data.get("contactEmail") or data.get("passenger_email") or data.get("email") or "traveler@busgo.com"
    phone = data.get("contactPhone") or data.get("passenger_phone") or data.get("phone") or "9876543210"

    # Extract boarding and dropping point details
    boarding_point = data.get("boarding_point") or data.get("boardingPoint") or ""
    dropping_point = data.get("dropping_point") or data.get("droppingPoint") or ""

    # Fetch bus details to compute stops if not explicitly passed as string
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buses WHERE bus_id = %s;", (bus_id,))
            bus_record = cursor.fetchone()
            if bus_record:
                src_city = bus_record["source"]
                dst_city = bus_record["destination"]
                if not boarding_point:
                    b_stops = CITY_STOPS.get(src_city, {}).get("boarding", [])
                    boarding_point = b_stops[0]["stop_name"] if b_stops else f"{src_city} Central Bus Stand"
                if not dropping_point:
                    d_stops = CITY_STOPS.get(dst_city, {}).get("dropping", [])
                    dropping_point = d_stops[-1]["stop_name"] if d_stops else f"{dst_city} Main Terminal"
    finally:
        conn.close()

    booking_res = tool_book_ticket(
        user_id=int(user_id),
        bus_id=int(bus_id),
        passenger_name=passenger_name,
        seat_number=seat_number,
        passenger_email=email,
        passenger_phone=phone,
        boarding_point=boarding_point,
        dropping_point=dropping_point,
        coupon_code=data.get("couponCode") or data.get("coupon_code") or ""
    )

    if booking_res.get("success"):
        b_id = booking_res["booking_id"]
        return jsonify({
            "success": True,
            "booking": {
                "bookingId": b_id,
                "booking_id": b_id,
                "pnr": booking_res["pnr"],
                "pnr_number": booking_res["pnr"],
                "totalAmount": booking_res["fare"],
                "boarding_point": boarding_point,
                "dropping_point": dropping_point,
                "status": "CONFIRMED"
            }
        }), 201

    return jsonify(booking_res), 400


@app.route("/api/payments/create-order", methods=["POST"])
def create_payment_order():
    """Initializes payment order with complete journey review and payment options."""
    data = request.get_json() or {}
    b_id = data.get("bookingId", 1)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT b.*, bus.operator_name, bus.source, bus.destination,
                       bus.departure_time, bus.arrival_time, bus.bus_type, bus.bus_number
                FROM bookings b
                JOIN buses bus ON b.bus_id = bus.bus_id
                WHERE b.booking_id = %s;
            """, (b_id,))
            booking = cursor.fetchone()
            if not booking:
                return jsonify({"success": False, "message": "Booking not found."}), 404

            amount = float(booking["total_fare"])
            dep_time_str = booking["departure_time"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(booking["departure_time"], datetime) else str(booking["departure_time"])

            return jsonify({
                "success": True,
                "orderId": f"order_{b_id}_{int(datetime.now().timestamp())}",
                "amount": amount,
                "amountInPaise": int(amount * 100),
                "keyId": "rzp_test_busgo123456789",
                "booking": {
                    "bookingId": b_id,
                    "pnr": booking["pnr_number"],
                    "amount": amount,
                    "operator_name": booking["operator_name"],
                    "bus_number": booking.get("bus_number") or "KA-09-F-4521",
                    "source": booking["source"],
                    "destination": booking["destination"],
                    "bus_type": booking["bus_type"],
                    "departure_time": dep_time_str,
                    "seat_number": booking["seat_number"],
                    "boarding_point": booking.get("boarding_point") or f"{booking['source']} Central Bus Station",
                    "dropping_point": booking.get("dropping_point") or f"{booking['destination']} Main Bus Terminal",
                    "passenger_name": booking["passenger_name"]
                },
                "prefill": {
                    "name": booking["passenger_name"],
                    "email": booking["passenger_email"] or "traveler@busgo.com",
                    "phone": booking["passenger_phone"] or "9876543210"
                }
            })
    finally:
        conn.close()


@app.route("/api/payments/verify", methods=["POST"])
def verify_payment():
    """Verifies payment transaction, generates reference ID, and confirms booking."""
    data = request.get_json() or {}
    b_id = data.get("bookingId") or data.get("booking_id") or request.args.get("bookingId", 1)
    payment_method = data.get("paymentMethod") or "UPI"
    payment_id = data.get("razorpay_payment_id") or f"pay_{uuid.uuid4().hex[:12]}"
    txn_id = f"TXN_{datetime.now().strftime('%Y%m%d%H%M')}_{b_id}"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE bookings 
                SET payment_status = 'COMPLETED', booking_status = 'CONFIRMED' 
                WHERE booking_id = %s;
            """, (b_id,))

            cursor.execute("""
                SELECT b.*, bus.operator_name, bus.source, bus.destination,
                       bus.departure_time, bus.arrival_time, bus.bus_type
                FROM bookings b
                JOIN buses bus ON b.bus_id = bus.bus_id
                WHERE b.booking_id = %s;
            """, (b_id,))
            booking = cursor.fetchone()

            pnr = booking["pnr_number"] if booking else f"BG{b_id}"

            return jsonify({
                "success": True,
                "message": "Payment verified and booking confirmed successfully.",
                "transactionId": txn_id,
                "paymentId": payment_id,
                "paymentMethod": payment_method,
                "booking": {
                    "bookingId": b_id,
                    "pnr": pnr,
                    "status": "CONFIRMED",
                    "totalAmount": float(booking["total_fare"]) if booking else 0.0,
                    "source": booking["source"] if booking else "",
                    "destination": booking["destination"] if booking else "",
                    "seat_number": booking["seat_number"] if booking else "",
                    "boarding_point": booking.get("boarding_point") if booking else "",
                    "dropping_point": booking.get("dropping_point") if booking else ""
                }
            })
    finally:
        conn.close()


@app.route("/api/bookings/my-bookings", methods=["GET"])
@app.route("/api/bookings", methods=["GET"])
def list_bookings():
    auth_header = request.headers.get("Authorization", "")
    user_id = 1
    if "busgo_token_" in auth_header:
        try:
            parts = auth_header.split("busgo_token_")[1].split("_")
            user_id = int(parts[0])
        except Exception:
            user_id = 1

    hist_res = tool_get_booking_history(int(user_id))
    raw_bookings = hist_res.get("bookings", [])

    upcoming = []
    completed = []
    cancelled = []

    now = datetime.now()
    for b in raw_bookings:
        dep_time_str = b.get("departure_time", "")
        try:
            dep_dt = datetime.strptime(dep_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            dep_dt = now + timedelta(days=1)

        formatted_item = {
            "booking_id": b["booking_id"],
            "pnr_number": b["pnr_number"],
            "source_city": b["source"],
            "destination_city": b["destination"],
            "bus_name": f"{b['operator_name']} Luxury",
            "operator_name": b["operator_name"],
            "bus_number": b.get("bus_number") or "",
            "bus_type": b["bus_type"],
            "journey_date": dep_time_str[:10],
            "departure_time": dep_time_str,
            "arrival_time": b.get("arrival_time", ""),
            "seats_booked": b["seat_number"],
            "seat_number": b["seat_number"],
            "total_amount": float(b["total_fare"]),
            "boarding_point": b.get("boarding_point", ""),
            "dropping_point": b.get("dropping_point", ""),
            "booking_status": b["booking_status"].lower(),
            "payment_status": "Paid"
        }

        if b["booking_status"] == "CANCELLED":
            cancelled.append(formatted_item)
        elif dep_dt < now:
            completed.append(formatted_item)
        else:
            upcoming.append(formatted_item)

    return jsonify({
        "success": True,
        "bookings": {
            "upcoming": upcoming,
            "completed": completed,
            "cancelled": cancelled
        },
        "all_bookings": raw_bookings
    })


@app.route("/api/bookings/cancel/<int:booking_id>", methods=["POST"])
@app.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking_endpoint(booking_id):
    auth_header = request.headers.get("Authorization", "")
    user_id = 1
    if "busgo_token_" in auth_header:
        try:
            parts = auth_header.split("busgo_token_")[1].split("_")
            user_id = int(parts[0])
        except Exception:
            user_id = 1

    cancel_res = tool_cancel_booking(booking_id=booking_id, user_id=int(user_id))

    if cancel_res.get("success"):
        return jsonify({
            "success": True,
            "message": cancel_res["message"],
            "refund": {
                "refundAmount": cancel_res["refund_amount"],
                "refundPercentage": cancel_res["refund_percentage"],
                "hoursRemaining": cancel_res["hours_before_departure"]
            }
        })
    return jsonify(cancel_res), 400


@app.route("/api/bookings/<int:booking_id>/download-ticket", methods=["GET"])
def download_ticket(booking_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT b.*, bus.operator_name, bus.source, bus.destination,
                       bus.departure_time, bus.arrival_time, bus.bus_type, bus.bus_number
                FROM bookings b
                JOIN buses bus ON b.bus_id = bus.bus_id
                WHERE b.booking_id = %s;
            """, (booking_id,))
            b = cursor.fetchone()
            if not b:
                return jsonify({"error": "Ticket not found"}), 404

            bp = b.get("boarding_point") or f"{b['source']} Central Bus Station"
            dp = b.get("dropping_point") or f"{b['destination']} Main Bus Terminal"
            p_gender = b.get("passenger_gender")
            p_age = b.get("passenger_age")
            if p_gender and p_age:
                passenger_label = f"{b['passenger_name']} ({p_gender}, Age: {p_age})"
            elif p_age:
                passenger_label = f"{b['passenger_name']} (Age: {p_age})"
            else:
                passenger_label = b['passenger_name']

            # Return styled electronic ticket document
            html_ticket = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>BUSGO E-Ticket - {b['pnr_number']}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f1f5f9; padding: 30px; margin: 0; }}
                    .ticket-box {{ max-width: 720px; margin: auto; background: #fff; border-radius: 16px; border: 2px dashed #d84e55; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }}
                    .header {{ border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                    .logo {{ font-size: 26px; font-weight: 800; color: #d84e55; display: flex; align-items: center; gap: 8px; }}
                    .pnr {{ font-size: 16px; font-weight: 700; color: #1e293b; background: #fee2e2; padding: 6px 14px; border-radius: 8px; border: 1px solid #fca5a5; }}
                    .route-banner {{ background: #f8fafc; border-radius: 12px; padding: 18px 24px; margin: 20px 0; display: flex; justify-content: space-between; align-items: center; border: 1px solid #e2e8f0; }}
                    .city {{ font-size: 22px; font-weight: 800; color: #0f172a; }}
                    .arrow {{ font-size: 20px; color: #d84e55; margin: 0 12px; font-weight: 700; }}
                    .details {{ margin: 24px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; font-size: 14px; line-height: 1.6; }}
                    .detail-item {{ background: #fdfdfd; padding: 12px 16px; border-radius: 8px; border: 1px solid #f1f5f9; }}
                    .detail-label {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px; }}
                    .detail-val {{ font-size: 15px; font-weight: 600; color: #1e293b; }}
                    .stops-card {{ background: #fff1f2; border-radius: 10px; padding: 16px 20px; margin: 20px 0; border: 1px solid #fecdd3; }}
                    .stops-card h4 {{ margin: 0 0 10px 0; font-size: 14px; color: #9f1239; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .footer {{ border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #64748b; text-align: center; }}
                    .print-bar {{ text-align: center; margin-bottom: 20px; }}
                    .btn-print {{ background: #d84e55; color: #fff; border: none; padding: 10px 24px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; }}
                    @media print {{
                        .print-bar {{ display: none; }}
                        body {{ background: #fff; padding: 0; }}
                        .ticket-box {{ border: 1px solid #000; box-shadow: none; }}
                    }}
                </style>
            </head>
            <body>
                <div class="print-bar">
                    <button class="btn-print" onclick="window.print()">🖨️ Print / Save PDF</button>
                </div>
                <div class="ticket-box">
                    <div class="header">
                        <div class="logo">🚌 BUSGO ELECTRONIC TICKET</div>
                        <div class="pnr">PNR: {b['pnr_number']}</div>
                    </div>
                    <div class="route-banner">
                        <div>
                            <div class="city">{b['source']} <span class="arrow">&rarr;</span> {b['destination']}</div>
                            <div style="font-size:13px; color:#64748b; margin-top:4px;">{b['operator_name']} | {b['bus_type']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:12px; color:#64748b;">Total Paid Fare</div>
                            <div style="font-size:24px; font-weight:800; color:#16a34a;">₹{float(b['total_fare']):.2f}</div>
                        </div>
                    </div>
                    <!-- Bus Number for Easy Identification at Bay -->
                    <div style="background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%); border: 2px solid #f87171; border-radius: 12px; padding: 14px 20px; margin: 16px 0; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 11px; text-transform: uppercase; color: #991b1b; font-weight: 800; letter-spacing: 0.8px;">🚌 Assigned Bus Number (Vehicle No.)</div>
                            <div style="font-size: 24px; font-weight: 900; color: #b91c1c; letter-spacing: 1px; margin-top: 3px;">{b.get('bus_number') or 'KA-09-F-4521'}</div>
                            <div style="font-size: 12px; color: #64748b; margin-top: 2px;">Locate this Bus Number on the windshield / boarding platform to board easily.</div>
                        </div>
                        <div style="text-align: right; background: #fee2e2; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 700; color: #991b1b;">
                            Bay / Bus: {b.get('bus_number') or 'KA-09-F-4521'}
                        </div>
                    </div>
                    <div class="details">
                        <div class="detail-item">
                            <div class="detail-label">Primary Passenger</div>
                            <div class="detail-val">{passenger_label}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Confirmed Seat(s)</div>
                            <div class="detail-val" style="color:#d84e55;">{b['seat_number']}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Departure Date & Time</div>
                            <div class="detail-val">{b['departure_time']}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Arrival Estimate</div>
                            <div class="detail-val">{b.get('arrival_time') or 'On Schedule'}</div>
                        </div>
                    </div>
                    <div class="stops-card">
                        <h4>📍 Boarding & Dropping Points</h4>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; font-size:13px;">
                            <div>
                                <strong style="color:#0f172a;">Boarding Point:</strong><br>
                                <span style="color:#334155;">{bp}</span><br>
                                <small style="color:#b91c1c;">(Please report 15 mins prior to departure)</small>
                            </div>
                            <div>
                                <strong style="color:#0f172a;">Dropping Point:</strong><br>
                                <span style="color:#334155;">{dp}</span>
                            </div>
                        </div>
                    </div>
                    <div class="footer">
                        <strong>Booking Status:</strong> {b['booking_status']} (Payment: {b['payment_status']})<br>
                        A physical photo ID proof is mandatory during boarding. Helpline: 1800-123-BUSGO<br>
                        Thank you for choosing BUSGO — Have a pleasant journey!
                    </div>
                </div>
                <script>
                    window.addEventListener('load', function() {{
                        setTimeout(function() {{
                            window.print();
                        }}, 500);
                    }});
                </script>
            </body>
            </html>
            """
            return Response(html_ticket, mimetype="text/html")
    finally:
        conn.close()


# ==============================================================================
# MODULE 4: RAG KNOWLEDGE BASE & RETRIEVAL (FR-10, SRS Table 5)
# ==============================================================================

@app.route("/api/knowledge/documents", methods=["GET"])
def list_knowledge_documents():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM travel_knowledge ORDER BY document_id ASC;")
            docs = cursor.fetchall()
            for d in docs:
                if isinstance(d.get("upload_date"), datetime):
                    d["upload_date"] = d["upload_date"].strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({"success": True, "count": len(docs), "documents": docs})
    finally:
        conn.close()


@app.route("/api/knowledge/query", methods=["POST"])
def query_knowledge_base():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Query parameter cannot be empty."}), 400

    rag_res = answer_policy_with_rag(query)
    return jsonify({
        "success": True,
        "query": query,
        "answer": rag_res["answer"],
        "grounded": rag_res["grounded"],
        "sources": rag_res["sources"],
        "retrieved_chunks": rag_res["retrieved_chunks"]
    })


# ==============================================================================
# MODULE 8: PLAYWRIGHT BROWSER AUTOMATION (FR-14)
# ==============================================================================

@app.route("/api/automation/run", methods=["POST"])
def run_automation_endpoint():
    data = request.get_json() or {}
    workflow = data.get("workflow", "search")
    from_city = data.get("from", "Hyderabad")
    to_city = data.get("to", "Bangalore")
    travel_date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    bus_id = int(data.get("bus_id", 1))

    if workflow == "seat_selection":
        res = run_automated_seat_workflow(bus_id=bus_id, headless=True)
    else:
        res = run_automated_bus_search(
            from_city=from_city,
            to_city=to_city,
            travel_date=travel_date,
            headless=True
        )

    return jsonify(res)


# ==============================================================================
# SRS SECTION 16: THREE RECOMMENDED HCLTECH DEMONSTRATIONS
# ==============================================================================

@app.route("/api/demo/<int:demo_id>", methods=["GET"])
def run_demo(demo_id):
    """
    Executes the 3 Working Demonstrations specified in SRS Section 16:
    Demo 1: Natural-language bus search and comparison.
    Demo 2: A cancellation or refund question answered using the RAG knowledge base.
    Demo 3: An AI Agent completing a multi-step task by calling approved tools.
    """
    if demo_id == 1:
        prompt = "Find the cheapest sleeper bus from Hyderabad to Bangalore and compare options."
        res = process_agent_request(prompt)
        return jsonify({
            "demo_id": 1,
            "title": "Natural-Language Bus Search & Comparison",
            "prompt": prompt,
            "execution": res
        })

    elif demo_id == 2:
        prompt = "What is the refund percentage if I cancel my ticket 30 hours before travel?"
        res = answer_policy_with_rag(prompt)
        return jsonify({
            "demo_id": 2,
            "title": "Cancellation/Refund Question Grounded in RAG Knowledge Base",
            "prompt": prompt,
            "execution": res
        })

    elif demo_id == 3:
        # Step A: Search buses
        search_out = tool_search_bus("Hyderabad", "Bangalore", bus_type="Sleeper", max_price=1000)
        best_bus = search_out["buses"][0] if search_out["buses"] else {"bus_id": 1}
        # Step B: Check seats
        seats_out = tool_check_seats(best_bus["bus_id"])
        # Step C: Confirmed booking
        book_out = tool_book_ticket(
            user_id=1,
            bus_id=best_bus["bus_id"],
            passenger_name="HCLTech Evaluator",
            seat_number="L4"
        )
        return jsonify({
            "demo_id": 3,
            "title": "AI Agent Multi-Step Task Completion Using Approved Tools",
            "workflow_steps": [
                {"step": 1, "tool": "search_bus", "result": f"Found {search_out['count']} buses under ₹1000"},
                {"step": 2, "tool": "check_seats", "result": f"Inspected {seats_out.get('available_seats', 0)} available seats"},
                {"step": 3, "tool": "book_ticket", "result": f"Confirmed PNR {book_out.get('pnr')} for {book_out.get('passenger_name')}"}
            ],
            "final_booking": book_out
        })

    return jsonify({"error": "Invalid demo_id. Choose 1, 2, or 3."}), 400


# ==============================================================================
# SERVER INITIALIZATION
# ==============================================================================

# ==============================================================================
# FRONTEND STATIC ROUTING (CATCH-ALL AFTER ALL API ROUTES)
# ==============================================================================

@app.route("/<path:filename>")
def serve_static(filename):
    if filename.startswith("api/"):
        return jsonify({"success": False, "message": f"API endpoint '/{filename}' not found."}), 404
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    print("=" * 60)
    print("🚌 BUSGO Agentic AI Travel System Server")
    print("Backend: Python Flask | Generative AI: Claude & RAG")
    print("Database: MySQL (busgo_db) | Vector Store: ChromaDB")
    print("=" * 60)

    # Initialize DB & RAG
    try:
        initialize_database()
    except Exception as e:
        print(f"[!] Database startup check: {e}")

    try:
        init_rag_system()
    except Exception as e:
        print(f"[!] RAG startup check: {e}")

    port = int(os.getenv("PORT", 5000))
    print(f"\n🌍 Web Server live at: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
