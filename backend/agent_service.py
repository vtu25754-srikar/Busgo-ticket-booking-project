"""
BUSGO AI Agent Service (Claude AI + Tool Calling)
Implements SRS Module 2, Module 3, Module 5 & Module 10:
- Conversational travel assistant
- Natural language entity extraction (source, destination, date, bus type, budget)
- Predefined approved tools:
    1. search_bus(source, destination, date, bus_type, max_price)
    2. compare_bus(source, destination, date, sort_by)
    3. check_seats(bus_id)
    4. get_booking_history(user_id)
    5. search_travel_policy(query)
    6. book_ticket(bus_id, passenger_name, seat_number, user_id)
    7. cancel_booking(booking_id, user_id)
- Multi-step tool execution coordinated by the backend.
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pymysql

from init_db import get_connection
from rag_service import answer_policy_with_rag, is_travel_related_policy_query

# Anthropic Claude setup
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
claude_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print("[+] Claude API Client initialized with key.")
    except Exception as e:
        print(f"[!] Anthropic SDK initialization warning: {e}")


# ==============================================================================
# APPROVED BACKEND TOOLS IMPLEMENTATION (SRS Module 5)
# ==============================================================================

def tool_search_bus(
    source: str,
    destination: str,
    date: Optional[str] = None,
    bus_type: Optional[str] = None,
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Approved Tool: search_bus
    Searches available bus records from MySQL based on extracted travel details.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM buses WHERE LOWER(source) = LOWER(%s) AND LOWER(destination) = LOWER(%s)"
            params = [source.strip(), destination.strip()]

            if date:
                query += " AND DATE(departure_time) = %s"
                params.append(date.strip())
            else:
                # Default to today or future
                query += " AND departure_time >= NOW()"

            if bus_type:
                b_type = bus_type.lower()
                if "sleeper" in b_type:
                    query += " AND bus_type LIKE %s"
                    params.append("%Sleeper%")
                elif "seater" in b_type:
                    query += " AND bus_type LIKE %s"
                    params.append("%Seater%")
                if "non-ac" in b_type or "non ac" in b_type:
                    query += " AND bus_type LIKE %s"
                    params.append("%Non-AC%")
                elif "ac" in b_type:
                    query += " AND bus_type LIKE %s"
                    params.append("%AC%")

            if max_price:
                query += " AND price <= %s"
                params.append(float(max_price))

            query += " ORDER BY price ASC LIMIT 10;"
            cursor.execute(query, params)
            buses = cursor.fetchall()

            # Format datetime objects for JSON serialization
            for b in buses:
                if isinstance(b.get("departure_time"), datetime):
                    b["departure_time"] = b["departure_time"].strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(b.get("arrival_time"), datetime):
                    b["arrival_time"] = b["arrival_time"].strftime("%Y-%m-%d %H:%M:%S")
                if "price" in b:
                    b["price"] = float(b["price"])
                if "rating" in b:
                    b["rating"] = float(b["rating"])

            return {
                "success": True,
                "tool": "search_bus",
                "count": len(buses),
                "criteria": {
                    "source": source,
                    "destination": destination,
                    "date": date,
                    "bus_type": bus_type,
                    "max_price": max_price
                },
                "buses": buses
            }
    finally:
        conn.close()


def tool_compare_bus(
    source: str,
    destination: str,
    date: Optional[str] = None,
    sort_by: str = "price_asc"
) -> Dict[str, Any]:
    """
    Approved Tool: compare_bus
    Compares buses based on price, departure time, bus type and ratings.
    """
    search_res = tool_search_bus(source, destination, date)
    buses = search_res.get("buses", [])

    if not buses:
        return {
            "success": True,
            "tool": "compare_bus",
            "message": f"No buses found between {source} and {destination} to compare.",
            "comparison": []
        }

    # Sorting
    if sort_by == "price_asc" or sort_by == "cheapest":
        buses.sort(key=lambda x: x["price"])
    elif sort_by == "price_desc":
        buses.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "rating_desc" or sort_by == "highest_rated":
        buses.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "departure_asc" or sort_by == "earliest":
        buses.sort(key=lambda x: x["departure_time"])

    cheapest = min(buses, key=lambda x: x["price"])
    highest_rated = max(buses, key=lambda x: x["rating"])

    return {
        "success": True,
        "tool": "compare_bus",
        "total_buses": len(buses),
        "cheapest_option": cheapest,
        "highest_rated_option": highest_rated,
        "comparison_table": buses
    }


def tool_check_seats(bus_id: int) -> Dict[str, Any]:
    """
    Approved Tool: check_seats
    Retrieves real-time deck layout and seat availability for a bus.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buses WHERE bus_id = %s;", (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return {"success": False, "message": f"Bus ID {bus_id} not found."}

            cursor.execute("""
                SELECT seat_number, deck, seat_type, is_booked, is_ladies 
                FROM seat_reservations 
                WHERE bus_id = %s;
            """, (bus_id,))
            booked_rows = cursor.fetchall()
            booked_map = {r["seat_number"]: r for r in booked_rows}

            # Generate standard RedBus deck layout (Lower Deck: L1-L18, Upper Deck: U1-U18)
            lower_deck = []
            upper_deck = []

            for i in range(1, 19):
                # Lower deck seat
                s_id = f"L{i}"
                info = booked_map.get(s_id, {})
                lower_deck.append({
                    "seat_number": s_id,
                    "deck": "lower",
                    "type": "sleeper" if "Sleeper" in bus["bus_type"] else "seater",
                    "status": "booked" if info.get("is_booked") else ("ladies" if info.get("is_ladies") else "available"),
                    "price": float(bus["price"])
                })

                # Upper deck berth
                u_id = f"U{i}"
                u_info = booked_map.get(u_id, {})
                upper_deck.append({
                    "seat_number": u_id,
                    "deck": "upper",
                    "type": "sleeper",
                    "status": "booked" if u_info.get("is_booked") else ("ladies" if u_info.get("is_ladies") else "available"),
                    "price": float(bus["price"]) + 50.0  # slight premium for upper berth privacy
                })

            available_count = sum(1 for s in lower_deck + upper_deck if s["status"] == "available")

            return {
                "success": True,
                "tool": "check_seats",
                "bus_id": bus_id,
                "operator_name": bus["operator_name"],
                "bus_type": bus["bus_type"],
                "total_seats": len(lower_deck) + len(upper_deck),
                "available_seats": available_count,
                "decks": {
                    "lower": lower_deck,
                    "upper": upper_deck
                }
            }
    finally:
        conn.close()


def tool_get_booking_history(user_id: int) -> Dict[str, Any]:
    """
    Approved Tool: get_booking_history
    Retrieves stored booking records strictly for the authenticated user (FR-12, TC-10).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT email, phone FROM users WHERE user_id = %s;", (user_id,))
            u_info = cursor.fetchone()
            u_email = u_info.get("email", "") if u_info else ""
            u_phone = u_info.get("phone", "") if u_info else ""

            if u_email or u_phone:
                cursor.execute("""
                    SELECT b.booking_id, b.pnr_number, b.passenger_name, b.seat_number,
                           b.boarding_point, b.dropping_point,
                           b.booking_date, b.booking_status, b.total_fare,
                           bus.operator_name, bus.source, bus.destination,
                           bus.departure_time, bus.arrival_time, bus.bus_type,
                           bus.bus_number
                    FROM bookings b
                    JOIN buses bus ON b.bus_id = bus.bus_id
                    WHERE b.user_id = %s 
                       OR (b.passenger_email != '' AND b.passenger_email = %s)
                       OR (b.passenger_phone != '' AND b.passenger_phone = %s)
                    ORDER BY b.booking_date DESC;
                """, (user_id, u_email, u_phone))
            else:
                cursor.execute("""
                    SELECT b.booking_id, b.pnr_number, b.passenger_name, b.seat_number,
                           b.boarding_point, b.dropping_point,
                           b.booking_date, b.booking_status, b.total_fare,
                           bus.operator_name, bus.source, bus.destination,
                           bus.departure_time, bus.arrival_time, bus.bus_type,
                           bus.bus_number
                    FROM bookings b
                    JOIN buses bus ON b.bus_id = bus.bus_id
                    WHERE b.user_id = %s
                    ORDER BY b.booking_date DESC;
                """, (user_id,))
            bookings = cursor.fetchall()

            for b in bookings:
                if isinstance(b.get("booking_date"), datetime):
                    b["booking_date"] = b["booking_date"].strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(b.get("departure_time"), datetime):
                    b["departure_time"] = b["departure_time"].strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(b.get("arrival_time"), datetime):
                    b["arrival_time"] = b["arrival_time"].strftime("%Y-%m-%d %H:%M:%S")
                if "total_fare" in b:
                    b["total_fare"] = float(b["total_fare"])

            return {
                "success": True,
                "tool": "get_booking_history",
                "user_id": user_id,
                "count": len(bookings),
                "bookings": bookings
            }
    finally:
        conn.close()


# ==============================================================================
# PROMOTIONAL COUPONS & APPLICABILITY ENGINE
# ==============================================================================

AVAILABLE_COUPONS = [
    {
        "code": "FIRST10",
        "title": "10% OFF",
        "discount_type": "percent",
        "value": 10,
        "max_discount": 200.0,
        "min_amount": 0.0,
        "description": "10% instant discount up to ₹200 on all routes",
        "badge": "POPULAR"
    },
    {
        "code": "SAVE100",
        "title": "FLAT ₹100 OFF",
        "discount_type": "flat",
        "value": 100.0,
        "max_discount": 100.0,
        "min_amount": 500.0,
        "description": "Flat ₹100 instant discount on bookings of ₹500+",
        "badge": "BEST VALUE"
    },
    {
        "code": "SUMMER20",
        "title": "20% OFF",
        "discount_type": "percent",
        "value": 20,
        "max_discount": 300.0,
        "min_amount": 0.0,
        "description": "20% seasonal travel discount up to ₹300",
        "badge": "HOLIDAY"
    },
    {
        "code": "BUSGO50",
        "title": "FLAT ₹50 OFF",
        "discount_type": "flat",
        "value": 50.0,
        "max_discount": 50.0,
        "min_amount": 0.0,
        "description": "Flat ₹50 instant savings, no minimum booking",
        "badge": "INSTANT"
    }
]


def evaluate_coupon(code: str, total_amount: float) -> Dict[str, Any]:
    """
    Evaluates coupon validity against order total and calculates discount amount.
    """
    code_upper = (code or "").strip().upper()
    if not code_upper:
        return {"valid": False, "discount": 0.0, "message": "No coupon code provided."}

    match = next((c for c in AVAILABLE_COUPONS if c["code"] == code_upper), None)
    if not match:
        return {
            "valid": False,
            "discount": 0.0,
            "message": f"Coupon code '{code_upper}' is invalid. Try FIRST10, SAVE100, SUMMER20, or BUSGO50."
        }

    if total_amount < match["min_amount"]:
        return {
            "valid": False,
            "discount": 0.0,
            "message": f"Coupon {match['code']} requires a minimum booking amount of ₹{match['min_amount']:.0f}."
        }

    if match["discount_type"] == "percent":
        discount = round(total_amount * (match["value"] / 100.0), 2)
        if match.get("max_discount"):
            discount = min(discount, match["max_discount"])
    else:
        discount = float(match["value"])

    discount = min(discount, total_amount)
    final_amount = max(0.0, round(total_amount - discount, 2))

    return {
        "valid": True,
        "code": match["code"],
        "discount": discount,
        "final_amount": final_amount,
        "message": f"Coupon {match['code']} applied! You saved ₹{discount:.2f}."
    }


def get_applicable_coupons(total_amount: float) -> List[Dict[str, Any]]:
    """
    Returns list of applicable coupons for passenger sorted by highest savings first.
    """
    suggested = []
    for c in AVAILABLE_COUPONS:
        res = evaluate_coupon(c["code"], total_amount)
        if res["valid"]:
            suggested.append({
                "code": c["code"],
                "title": c["title"],
                "badge": c["badge"],
                "description": c["description"],
                "discount_amount": res["discount"],
                "savings_text": f"Save ₹{res['discount']:.2f}"
            })
    suggested.sort(key=lambda x: x["discount_amount"], reverse=True)
    return suggested


def tool_book_ticket(
    user_id: int,
    bus_id: int,
    passenger_name: str,
    seat_number: str,
    passenger_email: str = "",
    passenger_phone: str = "",
    boarding_point: str = "",
    dropping_point: str = "",
    passenger_age: int = None,
    passenger_gender: str = None,
    coupon_code: str = ""
) -> Dict[str, Any]:
    """
    Approved Tool: book_ticket
    Creates a pending booking record in MySQL, applies coupon discounts, and reserves the seat.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM buses WHERE bus_id = %s;", (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return {"success": False, "message": "Selected bus not found."}

            import secrets
            seat_clean = seat_number.replace('-', '').replace(' ', '').replace(',', '')
            pnr = f"BG{datetime.now().strftime('%m%d%H%M%S')}{secrets.token_hex(2).upper()}"

            seat_list = [s.strip() for s in str(seat_number).split(",") if s.strip()]
            num_seats = max(1, len(seat_list))
            base_fare = round(float(bus["price"]) * num_seats, 2)

            # Apply promotional coupon if provided
            discount = 0.0
            applied_code = None
            if coupon_code:
                c_eval = evaluate_coupon(coupon_code, base_fare)
                if c_eval["valid"]:
                    discount = c_eval["discount"]
                    applied_code = c_eval["code"]

            fare = max(0.0, round(base_fare - discount, 2))

            # Fallback default stops if not specified
            bp = boarding_point or f"{bus['source']} Central Bus Station"
            dp = dropping_point or f"{bus['destination']} Main Bus Terminal"
            p_email = passenger_email or f"{passenger_name.lower().replace(' ', '')}@busgo.com"
            p_phone = passenger_phone or "9876543210"

            # Ensure valid user_id exists in users table to satisfy foreign key constraint
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
            valid_user = cursor.fetchone()
            if not valid_user:
                cursor.execute("SELECT user_id FROM users ORDER BY user_id ASC LIMIT 1;")
                fallback_u = cursor.fetchone()
                effective_user_id = fallback_u["user_id"] if fallback_u else 1
            else:
                effective_user_id = user_id

            bus_num = bus.get("bus_number") or ""

            cursor.execute("""
                INSERT INTO bookings (
                    user_id, bus_id, passenger_name, passenger_age, passenger_gender,
                    passenger_email, passenger_phone, seat_number, boarding_point, dropping_point,
                    bus_number, booking_date, booking_status, total_fare, pnr_number, payment_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'PENDING', %s, %s, 'PENDING');
            """, (effective_user_id, bus_id, passenger_name, passenger_age, passenger_gender, p_email, p_phone, seat_number, bp, dp, bus_num, fare, pnr))

            booking_id = cursor.lastrowid

            # Mark individual seats as reserved
            for s_num in seat_list:
                s_deck = "upper" if s_num.upper().startswith("U") else "lower"
                s_type = "sleeper" if "Sleeper" in str(bus.get("bus_type", "")) else "seater"
                cursor.execute("""
                    INSERT INTO seat_reservations (bus_id, seat_number, deck, seat_type, is_booked, booking_id)
                    VALUES (%s, %s, %s, %s, 1, %s)
                    ON DUPLICATE KEY UPDATE is_booked = 1, booking_id = %s;
                """, (bus_id, s_num[:10], s_deck, s_type, booking_id, booking_id))

            # Decrement available seats count
            cursor.execute("UPDATE buses SET available_seats = GREATEST(0, available_seats - %s) WHERE bus_id = %s;", (num_seats, bus_id))

            return {
                "success": True,
                "tool": "book_ticket",
                "booking_id": booking_id,
                "pnr": pnr,
                "passenger_name": passenger_name,
                "passenger_age": passenger_age,
                "passenger_gender": passenger_gender,
                "seat_number": seat_number,
                "boarding_point": bp,
                "dropping_point": dp,
                "bus_operator": bus["operator_name"],
                "bus_number": bus_num,
                "bus_type": bus.get("bus_type", ""),
                "source": bus["source"],
                "destination": bus["destination"],
                "departure_time": bus["departure_time"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(bus["departure_time"], datetime) else str(bus["departure_time"]),
                "fare": fare,
                "original_fare": base_fare,
                "discount": discount,
                "coupon_code": applied_code,
                "status": "PENDING",
                "payment_status": "PENDING",
                "payment_url": f"/payment.html?bookingId={booking_id}",
                "num_seats": num_seats
            }
    finally:
        conn.close()


def tool_cancel_booking(booking_id: int, user_id: int) -> Dict[str, Any]:
    """
    Approved Tool: cancel_booking
    Cancels a booking and computes refund according to verified RAG cancellation policy.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT b.*, bus.departure_time, bus.operator_name, bus.price
                FROM bookings b
                JOIN buses bus ON b.bus_id = bus.bus_id
                WHERE b.booking_id = %s AND b.user_id = %s;
            """, (booking_id, user_id))
            booking = cursor.fetchone()

            if not booking:
                return {"success": False, "message": "Booking record not found or unauthorized access."}

            if booking["booking_status"] == "CANCELLED":
                return {"success": False, "message": "This booking has already been cancelled."}

            dep_time = booking["departure_time"]
            if isinstance(dep_time, str):
                dep_time = datetime.strptime(dep_time, "%Y-%m-%d %H:%M:%S")

            hours_remaining = (dep_time - datetime.now()).total_seconds() / 3600.0
            fare = float(booking["total_fare"])

            # Compute refund per knowledge base policy
            if hours_remaining > 72:
                refund_pct = 90
            elif hours_remaining >= 24:
                refund_pct = 50
            else:
                refund_pct = 0

            refund_amt = round((fare * refund_pct) / 100.0, 2)

            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'CANCELLED' 
                WHERE booking_id = %s;
            """, (booking_id,))

            # Release seat
            cursor.execute("""
                UPDATE seat_reservations 
                SET is_booked = 0, booking_id = NULL 
                WHERE booking_id = %s;
            """, (booking_id,))

            # Increment available seats
            cursor.execute("UPDATE buses SET available_seats = LEAST(total_seats, available_seats + 1) WHERE bus_id = %s;", (booking["bus_id"],))

            return {
                "success": True,
                "tool": "cancel_booking",
                "booking_id": booking_id,
                "pnr": booking["pnr_number"],
                "hours_before_departure": round(hours_remaining, 1),
                "refund_percentage": f"{refund_pct}%",
                "refund_amount": refund_amt,
                "original_fare": fare,
                "status": "CANCELLED",
                "message": f"Ticket {booking['pnr_number']} cancelled successfully. {refund_pct}% refund of ₹{refund_amt} will be credited to original payment source within 3-5 business days."
            }
    finally:
        conn.close()


CITY_ALIASES = {
    # Hyderabad
    "hydrabad": "Hyderabad",
    "hyderbad": "Hyderabad",
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "secunderabad": "Hyderabad",
    # Bangalore
    "banglore": "Bangalore",
    "bengaluru": "Bangalore",
    "bengalooru": "Bangalore",
    "bangalore": "Bangalore",
    "blr": "Bangalore",
    # Chennai
    "chennai": "Chennai",
    "chenai": "Chennai",
    "madras": "Chennai",
    "maa": "Chennai",
    # Vijayawada
    "vijayawada": "Vijayawada",
    "vijaywada": "Vijayawada",
    "bezawada": "Vijayawada",
    "vja": "Vijayawada",
    # Visakhapatnam
    "visakhapatnam": "Visakhapatnam",
    "vishakapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "visakha": "Visakhapatnam",
    # Tirupati
    "tirupati": "Tirupati",
    "tirupathi": "Tirupati",
    "tpt": "Tirupati",
    # Coimbatore
    "coimbatore": "Coimbatore",
    "coimbator": "Coimbatore",
    "kovai": "Coimbatore",
    "cbe": "Coimbatore",
    # Madurai
    "madurai": "Madurai",
    "mdu": "Madurai",
    # Kochi
    "kochi": "Kochi",
    "cochin": "Kochi",
    "ernakulam": "Kochi",
    # Mysore
    "mysore": "Mysore",
    "mysuru": "Mysore",
    # Kurnool
    "kurnool": "Kurnool",
    "karnool": "Kurnool",
    # Mumbai
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    # Pune
    "pune": "Pune",
    "poona": "Pune",
    # Goa
    "goa": "Goa",
    "panaji": "Goa",
    # Delhi
    "delhi": "Delhi",
    # Jaipur
    "jaipur": "Jaipur",
}

# Multi-turn booking session cache (keyed by user_id)
PENDING_BOOKING_SESSIONS: Dict[int, Dict[str, Any]] = {}


def get_city_stops(city: str) -> Dict[str, List[str]]:
    """Returns lists of boarding and dropping points for a given city."""
    if not city:
        return {"boarding": [], "dropping": []}
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT boarding_point_name FROM boarding_points WHERE city_name = %s ORDER BY boarding_id ASC;", (city,))
            bps = [r["boarding_point_name"] for r in cursor.fetchall()]
            cursor.execute("SELECT dropping_point_name FROM dropping_points WHERE city_name = %s ORDER BY dropping_id ASC;", (city,))
            dps = [r["dropping_point_name"] for r in cursor.fetchall()]
            return {"boarding": bps, "dropping": dps}
    finally:
        conn.close()


def match_stop_to_city(term: Optional[str], city: str, is_boarding: bool = True) -> str:
    """Matches a user input stop term to official city boarding or dropping points."""
    stops = get_city_stops(city)
    list_to_search = stops["boarding"] if is_boarding else stops["dropping"]
    if not term:
        return list_to_search[0] if list_to_search else (f"{city} Central Bus Station" if is_boarding else f"{city} Main Bus Terminal")

    t_clean = term.lower().replace("-", " ").replace("–", " ").strip()
    for s in list_to_search:
        s_clean = s.lower().replace("-", " ").replace("–", " ").strip()
        if t_clean in s_clean or s_clean in t_clean:
            return s
        words = [w for w in t_clean.split() if len(w) > 2]
        if words and any(w in s_clean for w in words):
            return s
    return term.strip().title()


def parse_passenger_details(text: str, source_city: str = "", dest_city: str = "") -> Dict[str, Any]:
    """
    Extracts passenger name, age, gender, boarding point, and dropping point from conversational input.
    """
    details = {
        "name": None,
        "age": None,
        "gender": None,
        "boarding": None,
        "dropping": None,
        "seat": None,
        "coupon": None
    }

    # 1. Gender
    gm = re.search(r'\b(?:gender|sex)[:\s=]+(female|male|transgender|other|m|f)\b', text, re.IGNORECASE)
    if gm:
        val = gm.group(1).lower()
        details["gender"] = "Female" if val in ["female", "f"] else ("Male" if val in ["male", "m"] else "Other")
    elif re.search(r'\b(female)\b', text, re.IGNORECASE):
        details["gender"] = "Female"
    elif re.search(r'\b(male)\b', text, re.IGNORECASE):
        details["gender"] = "Male"
    elif re.search(r'\b(transgender|other)\b', text, re.IGNORECASE):
        details["gender"] = "Other"

    # 2. Age
    am = re.search(r'\bage[:\s=]*(\d{1,2})\b', text, re.IGNORECASE)
    if am:
        details["age"] = int(am.group(1))
    else:
        am2 = re.search(r'\b(\d{1,2})\s*(?:yrs|years?|yo|year\s*old)\b', text, re.IGNORECASE)
        if am2:
            details["age"] = int(am2.group(1))

    # 3. Boarding point
    bm = re.search(r'(?:boarding(?:\s+point)?|pickup(?:\s+point|\s+area)?|from\s+point)[:\s=]+([a-zA-Z0-9\s\–\-]+?)(?=\s*,|\s+and|\s+drop|\s+to|\s+tomorrow|\.|$|;)', text, re.IGNORECASE)
    if bm:
        details["boarding"] = bm.group(1).strip()

    # 4. Dropping point
    dm = re.search(r'(?:dropping(?:\s+point)?|drop(?:\s+point|\s+area|\s+off)?|to\s+point)[:\s=]+([a-zA-Z0-9\s\–\-]+?)(?=\s*,|\s+and|\s+pickup|\s+boarding|\s+tomorrow|\.|$|;)', text, re.IGNORECASE)
    if dm:
        details["dropping"] = dm.group(1).strip()

    # 5. Name
    nm = re.search(r'(?:passenger\s+name|name|passenger)[:\s=]+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?=\s*(?:,|age|gender|sex|male|female|seat|berth|boarding|dropping|pickup|drop|price|budget|for|to|from|$))', text, re.IGNORECASE)
    if nm:
        cand = nm.group(1).strip().title()
        if cand.lower() not in ["ticket", "bus", "sleeper", "seater", "book", "under", "price"]:
            details["name"] = cand
    else:
        nm_start = re.search(r'(?:^|for\s+|passenger\s+|i am\s+)([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?=\s+age|\s*,\s*age|\s*,\s*\d{1,2})', text, re.IGNORECASE)
        if nm_start:
            cand = nm_start.group(1).strip().title()
            if cand.lower() not in ["ticket", "bus", "book", "chennai", "hyderabad", "bangalore", "mumbai", "pune"]:
                details["name"] = cand
        else:
            for_m = re.search(r'(?:for\s+)([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?=\s*(?:,|age|gender|sex|male|female|seat|berth|boarding|dropping|price|budget|$))', text, re.IGNORECASE)
            if for_m:
                cand = for_m.group(1).strip().title()
                if cand.lower() not in ["ticket", "bus", "sleeper", "seater", "me", "chennai", "hyderabad", "bangalore", "mumbai", "pune"]:
                    details["name"] = cand

    # 6. Preferred Seat or Berth number (e.g. "seat L3", "berth U2", "seat: L5")
    sm = re.search(r'\b(?:seat|berth)[:\s=]*([LU]\d{1,2})\b', text, re.IGNORECASE)
    if sm:
        details["seat"] = sm.group(1).upper()
    else:
        sm2 = re.search(r'\b([LU]\d{1,2})\b', text)
        if sm2:
            details["seat"] = sm2.group(1).upper()

    # Fallback comma-separated: "Srikar, 22, Male, Koyambedu, MGBS"
    parts = [p.strip() for p in text.split(',') if p.strip()]
    if len(parts) >= 2:
        non_keywords = []
        for idx, p in enumerate(parts):
            if not details["age"] and p.isdigit() and 1 <= int(p) <= 120:
                details["age"] = int(p)
            elif not details["name"] and idx == 0 and re.match(r'^[a-zA-Z\s]+$', p):
                words = p.split()
                if 1 <= len(words) <= 2 and not any(w.lower() in ["book", "ticket", "bus", "chennai", "hyderabad", "bangalore", "male", "female"] for w in words):
                    details["name"] = p.title()
            elif idx > 0 and not any(g in p.lower() for g in ["male", "female", "other"]) and not p.isdigit():
                non_keywords.append(p)
        if not details["boarding"] and len(non_keywords) >= 1:
            details["boarding"] = non_keywords[0]
        if not details["dropping"] and len(non_keywords) >= 2:
            details["dropping"] = non_keywords[1]

    # If boarding / dropping wasn't explicitly prefixed, match against city stops
    if source_city and not details["boarding"]:
        stops_src = get_city_stops(source_city)
        for s in stops_src.get("boarding", []):
            s_short = s.split("–")[0].split("-")[0].strip().lower()
            if s_short and s_short in text.lower():
                details["boarding"] = s
                break

    if dest_city and not details["dropping"]:
        stops_dst = get_city_stops(dest_city)
        for s in stops_dst.get("dropping", []):
            s_short = s.split("–")[0].split("-")[0].strip().lower()
            if s_short and s_short in text.lower():
                details["dropping"] = s
                break

    # 7. Promotional coupon code (e.g. "coupon FIRST10", "promo SAVE100", "code SUMMER20")
    cm = re.search(r'\b(?:coupon|promo|voucher|code)[:\s=]+([A-Za-z0-9]+)\b', text, re.IGNORECASE)
    if cm:
        details["coupon"] = cm.group(1).upper()
    else:
        for c_cand in ["FIRST10", "SAVE100", "SUMMER20", "BUSGO50"]:
            if re.search(rf'\b{c_cand}\b', text, re.IGNORECASE):
                details["coupon"] = c_cand
                break

    return details


def normalize_city_name(city: Optional[str]) -> Optional[str]:
    if not city:
        return None
    raw = re.sub(r'[^a-zA-Z]', '', str(city)).lower()
    if raw in CITY_ALIASES:
        return CITY_ALIASES[raw]
    for k, v in CITY_ALIASES.items():
        if k in raw or raw in k:
            return v
    return city.strip().title()


# ==============================================================================
# NATURAL LANGUAGE ENTITY & INTENT PARSER (SRS Module 2 & FR-04)
# ==============================================================================

def extract_travel_intent_and_entities(message: str) -> Dict[str, Any]:
    """
    Extracts origin, destination, date, bus type, and budget from conversational text.
    Example: 'Find a sleeper bus from Hyderabad to Bangalore on 20 November within a budget of 1,000 rupees.'
    """
    text = message.lower()
    entities = {
        "intent": "search_bus",
        "source": None,
        "destination": None,
        "date": None,
        "bus_type": None,
        "max_budget": None,
        "sort_by": None,
        "passenger_name": None,
        "passenger_age": None
    }

    # 1. Intent Detection
    if any(w in text for w in ["cancel", "refund", "hours", "policy", "luggage", "baggage", "weight", "pet", "id proof", "senior citizen"]):
        entities["intent"] = "travel_policy"
        return entities

    if any(w in text for w in ["my bookings", "booking history", "my trips", "past bookings", "show my tickets"]):
        entities["intent"] = "booking_history"
        return entities

    if any(w in text for w in ["book ticket", "book a ticket", "book bus", "reserve ticket", "reserve seat", "book me a ticket", "book a seat"]) or (text.startswith("book") and ("to" in text or "ticket" in text or "bus" in text)):
        entities["intent"] = "book_ticket"

    elif any(w in text for w in ["compare", "cheapest", "fastest", "best rated", "highest rated"]):
        entities["intent"] = "compare_bus"

    elif any(w in text for w in ["seat layout", "check seats", "seat availability", "available seats"]):
        entities["intent"] = "check_seats"

    # 2. Extract Cities (Origin -> Destination)
    known_cities = list(CITY_ALIASES.keys()) + [
        "hyderabad", "bangalore", "chennai", "mumbai", "pune", "delhi",
        "jaipur", "goa", "vijayawada", "vizag", "visakhapatnam", "chandigarh",
        "madurai", "coimbatore", "mysore", "mangalore", "lucknow",
        "tirupati", "shirdi", "kurnool", "kochi"
    ]

    # Match "from X to Y"
    from_to_match = re.search(r'from\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)', text)
    if from_to_match:
        c1, c2 = from_to_match.group(1).title(), from_to_match.group(2).title()
        entities["source"] = normalize_city_name(c1)
        entities["destination"] = normalize_city_name(c2)
    else:
        # Match "X to Y"
        to_match = re.search(r'([a-zA-Z]+)\s+to\s+([a-zA-Z]+)', text)
        if to_match and (to_match.group(1).lower() in known_cities or to_match.group(2).lower() in known_cities):
            entities["source"] = normalize_city_name(to_match.group(1))
            entities["destination"] = normalize_city_name(to_match.group(2))

    # Fallback city scan if only one matched
    if not entities["source"] or not entities["destination"]:
        found = []
        for c in set(known_cities):
            if re.search(r'\b' + re.escape(c) + r'\b', text):
                norm = normalize_city_name(c)
                if norm not in found:
                    found.append(norm)
        if len(found) >= 2:
            entities["source"] = found[0]
            entities["destination"] = found[1]
        elif len(found) == 1 and not entities["source"]:
            entities["source"] = found[0]

    # Clean up any stop words captured by regex
    invalid_city_words = ["ticket", "bus", "me", "a", "my", "seat", "seats", "near", "for", "please", "book", "under", "price"]
    if entities["source"] and entities["source"].lower() in invalid_city_words:
        entities["source"] = None
    if entities["destination"] and entities["destination"].lower() in invalid_city_words:
        entities["destination"] = None

    # 3. Extract Bus Type
    if "sleeper" in text:
        entities["bus_type"] = "AC Sleeper" if "ac" in text and "non" not in text else ("Non-AC Sleeper" if "non" in text else "Sleeper")
    elif "seater" in text:
        entities["bus_type"] = "AC Seater" if "ac" in text and "non" not in text else ("Non-AC Seater" if "non" in text else "Seater")
    elif "ac" in text and "non" not in text:
        entities["bus_type"] = "AC"

    # 4. Extract Budget / Price (ignore coupon discounts like -₹50 or coupon codes)
    clean_text_budget = re.sub(r'\(?-₹\s*\d+(?:\.\d+)?\)?', '', text)
    clean_text_budget = re.sub(r'coupon[^\n,;|]+', '', clean_text_budget, flags=re.IGNORECASE)
    clean_text_budget = re.sub(r'discount[^\n,;|]+', '', clean_text_budget, flags=re.IGNORECASE)

    budget_match = re.search(r'(?:budget(?:\s+of|\s+is|:)?|max(?:imum)?\s+(?:price|budget|fare)|cost(?:\s+under|\s+below|:)?|under|within|less\s+than|below|upto|up\s+to)\s*(?:rs\.?|inr|₹)?\s*(\d+[\d,]*)', clean_text_budget)
    if budget_match:
        entities["max_budget"] = float(budget_match.group(1).replace(",", ""))

    # 4b. Extract Passenger Name & Age (for booking prompt)
    name_patterns = [
        r'(?:name[:\s]+|passenger[:\s]+)\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?=\s*(?:age|price|budget|for|to|from|$))',
        r'(?:for\s+)([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?=\s*(?:age|price|budget|$))',
        r'(?:to\s+[a-zA-Z]+\s+)([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?=\s*age)'
    ]
    for np in name_patterns:
        m = re.search(np, message, re.IGNORECASE)
        if m:
            cand = m.group(1).strip().title()
            if cand.lower() not in ["ticket", "bus", "sleeper", "seater", "tomorrow", "today", "chennai", "bangalore", "hyderabad", "mumbai", "pune", "delhi", "vijayawada", "tirupati", "under", "price"]:
                entities["passenger_name"] = cand
                break

    age_m = re.search(r'age[:\s]*(\d{1,2})', text, re.IGNORECASE)
    if age_m:
        entities["passenger_age"] = int(age_m.group(1))

    # 5. Extract Date
    # Check for "day after tomorrow", "tomorrow", "today"
    today = datetime.now()
    if "day after tomorrow" in text:
        entities["date"] = (today + timedelta(days=2)).strftime("%Y-%m-%d")
    elif "tomorrow" in text:
        entities["date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "today" in text:
        entities["date"] = today.strftime("%Y-%m-%d")
    else:
        # Match e.g. "20 November", "20th Nov", "Nov 20", "November 20th"
        months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
        date_pattern = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*', text)
        date_pattern_rev = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?', text)
        if date_pattern:
            day = int(date_pattern.group(1))
            month_str = date_pattern.group(2)
            month = months.get(month_str, today.month)
            entities["date"] = f"{today.year}-{month:02d}-{day:02d}"
        elif date_pattern_rev:
            month_str = date_pattern_rev.group(1)
            day = int(date_pattern_rev.group(2))
            month = months.get(month_str, today.month)
            entities["date"] = f"{today.year}-{month:02d}-{day:02d}"
        else:
            iso_match = re.search(r'\b(202\d-\d{2}-\d{2})\b', text)
            dmy_match = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](202\d)\b', text)
            if iso_match:
                entities["date"] = iso_match.group(1)
            elif dmy_match:
                entities["date"] = f"{dmy_match.group(3)}-{int(dmy_match.group(2)):02d}-{int(dmy_match.group(1)):02d}"

    # 6. Extract Pickup & Drop Areas / Boarding & Dropping Points
    known_stops = [
        "ambattur", "koyambedu", "tambaram", "guindy", "madhavaram", "vadapalani", "anna nagar",
        "porur", "poonamallee", "avadi", "t nagar", "velachery", "sholinganallur", "kelambakkam",
        "electronic city", "majestic", "silk board", "madiwala", "marathahalli", "whitefield",
        "kr puram", "tin factory", "hebbal", "yeshwanthpur", "hsr layout", "btm layout",
        "mgbs", "jbs", "kukatpally", "miyapur", "ameerpet", "sr nagar", "lb nagar",
        "dilsukhnagar", "uppal", "gachibowli", "hitech city", "kondapur", "mehdipatnam",
        "lakdikapul", "shamshabad", "benz circle", "pnbs", "ramavarappadu", "gannavaram",
        "alipiri", "renigunta", "tirupati rtc", "rtc complex", "maddilapalem", "gajuwaka",
        "gandhipuram", "singanallur", "mattuthavani", "periyar", "arappalayam"
    ]

    pickup_match = re.search(r'(?:pick(?: me)? up near|pickup near|boarding at|from near)\s+([a-zA-Z\s]+?)(?=\s+and|\s+drop|\s+to|\s+tomorrow|\s+my budget|\.|$)', text)
    if pickup_match:
        entities["pickup_area"] = pickup_match.group(1).strip().title()
    else:
        for stop in known_stops:
            if f"near {stop}" in text or f"at {stop}" in text or f"from {stop}" in text:
                entities["pickup_area"] = stop.title()
                break

    drop_match = re.search(r'(?:drop(?: me)? near|drop near|dropping at|to near)\s+([a-zA-Z\s]+?)(?=\s+and|\s+tomorrow|\s+my budget|\.|$)', text)
    if drop_match:
        entities["drop_area"] = drop_match.group(1).strip().title()
    else:
        for stop in known_stops:
            if f"drop me near {stop}" in text or f"drop near {stop}" in text or f"to {stop}" in text:
                entities["drop_area"] = stop.title()
                break

    # 7. Extract Sort Criteria
    if "cheapest" in text or "lowest price" in text:
        entities["sort_by"] = "cheapest"
    elif "fastest" in text or "quickest" in text:
        entities["sort_by"] = "fastest"
    elif "rated" in text or "best" in text:
        entities["sort_by"] = "highest_rated"
    elif "earliest" in text:
        entities["sort_by"] = "earliest"

    return entities


# ==============================================================================
# AGENT COORDINATION & MULTI-STEP EXECUTION (SRS Module 5 & 10)
# ==============================================================================

def process_agent_request(user_message: str, user_id: Optional[int] = 1, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main Agent Entry Point:
    1. Interprets natural language request or in-chat interactive form data.
    2. Determines whether to execute an Approved Tool or query RAG Travel Knowledge.
    3. Executes the backend tool.
    4. Grounded response synthesis with conversational output and structured presentation.
    """
    entities = extract_travel_intent_and_entities(user_message)
    intent = entities["intent"]

    # 1. Travel Policy or FAQ Query -> Delegate to RAG System (SRS Module 4)
    if intent == "travel_policy" or is_travel_related_policy_query(user_message):
        rag_output = answer_policy_with_rag(user_message, claude_client)
        return {
            "success": True,
            "type": "policy_faq",
            "user_message": user_message,
            "tool_called": "search_travel_policy",
            "reply": rag_output["answer"],
            "sources": rag_output.get("sources", []),
            "grounded": rag_output.get("grounded", True)
        }

    # 2. Booking History Query
    if intent == "booking_history":
        hist_res = tool_get_booking_history(user_id=user_id or 1)
        b_count = hist_res.get("count", 0)
        bookings = hist_res.get("bookings", [])

        if b_count == 0:
            reply = "You do not have any active or past bus bookings stored in your BUSGO account yet."
        else:
            reply = f"Here is your travel booking history ({b_count} trip{'s' if b_count > 1 else ''} found):"

        return {
            "success": True,
            "type": "booking_history",
            "user_message": user_message,
            "tool_called": "get_booking_history",
            "reply": reply,
            "bookings": bookings
        }

    # 3. Bus Comparison Query
    if intent == "compare_bus":
        source = entities.get("source") or "Hyderabad"
        destination = entities.get("destination") or "Bangalore"
        date = entities.get("date")
        sort_by = entities.get("sort_by") or "cheapest"

        comp_res = tool_compare_bus(source, destination, date, sort_by=sort_by)
        buses = comp_res.get("comparison_table", [])
        cheapest = comp_res.get("cheapest_option")
        highest = comp_res.get("highest_rated_option")

        if not buses:
            reply = f"I could not find any buses between **{source}** and **{destination}** for comparison. Please try another popular route such as Hyderabad to Bangalore, or Mumbai to Pune."
        else:
            reply = (
                f"I compared **{len(buses)} available buses** from **{source}** to **{destination}**:\n\n"
                f"• **Cheapest Option:** **{cheapest['operator_name']}** ({cheapest['bus_type']}) at **₹{cheapest['price']:.2f}** (Departure: {cheapest['departure_time'][11:16]})\n"
                f"• **Highest Rated Option:** **{highest['operator_name']}** (⭐ {highest['rating']}/5.0) at **₹{highest['price']:.2f}**\n\n"
                f"Below is the complete comparison sorted by **{sort_by}**:"
            )

        return {
            "success": True,
            "type": "bus_comparison",
            "user_message": user_message,
            "tool_called": "compare_bus",
            "reply": reply,
            "cheapest": cheapest,
            "highest_rated": highest,
            "buses": buses
        }

    # 3b. Natural Language Direct Ticket Booking with Passenger Details & Payment Gateway
    active_session = PENDING_BOOKING_SESSIONS.get(user_id or 1)
    has_form_passengers = bool(form_data and form_data.get("passengers"))
    if intent == "book_ticket" or has_form_passengers or (active_session and intent not in ["travel_policy", "booking_history", "compare_bus"]):
        intent = "book_ticket"
        session = PENDING_BOOKING_SESSIONS.get(user_id or 1, {})

        source = (form_data.get("source") if form_data else None) or entities.get("source") or session.get("source")
        destination = (form_data.get("destination") if form_data else None) or entities.get("destination") or session.get("destination")

        if not source or not destination:
            return {
                "success": True,
                "type": "clarification_needed",
                "user_message": user_message,
                "tool_called": None,
                "reply": (
                    "To book your ticket, please specify your **Origin City** and **Destination City** "
                    "(e.g. *'Book ticket from Chennai to Hyderabad'*)."
                )
            }

        date = (form_data.get("date") if form_data else None) or entities.get("date") or session.get("date") or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        budget = entities.get("max_budget") or session.get("max_budget")
        bus_type = entities.get("bus_type") or session.get("bus_type")

        # Step 1: Search buses to verify availability
        if has_form_passengers or (form_data and form_data.get("bus_id")):
            # When form is being submitted, do not filter by budget to prevent accidental over_budget trigger
            search_res = tool_search_bus(source, destination, date=date)
        else:
            search_res = tool_search_bus(source, destination, date=date, max_price=budget, bus_type=bus_type)
        buses = search_res.get("buses", [])

        if not buses:
            fallback_res = tool_search_bus(source, destination, date=date)
            all_buses = fallback_res.get("buses", [])
            if not all_buses:
                PENDING_BOOKING_SESSIONS.pop(user_id or 1, None)
                return {
                    "success": True,
                    "type": "no_buses_found",
                    "user_message": user_message,
                    "tool_called": "search_bus",
                    "reply": f"Sorry, I could not find any active buses running from **{source}** to **{destination}** on **{date}**."
                }
            elif has_form_passengers:
                # If submitting passenger form, use all buses directly
                buses = all_buses
            else:
                min_price = min(b["price"] for b in all_buses)
                return {
                    "success": True,
                    "type": "over_budget",
                    "user_message": user_message,
                    "tool_called": "search_bus",
                    "reply": (
                        f"I found {len(all_buses)} buses from **{source}** to **{destination}**, "
                        f"but none under ₹{budget:.0f}. The lowest fare starts at **₹{min_price:.2f}**. "
                        f"Would you like me to book one of those?"
                    ),
                    "buses": all_buses[:3]
                }

        # Choose best bus
        buses_sorted = sorted(buses, key=lambda x: (x["price"], -x.get("rating", 4.0)))
        chosen_bus = buses_sorted[0]
        if form_data and form_data.get("bus_id"):
            req_bid = int(form_data["bus_id"])
            found_bus = next((b for b in buses if b["bus_id"] == req_bid), None)
            if found_bus:
                chosen_bus = found_bus
            else:
                conn_b = get_connection()
                try:
                    with conn_b.cursor() as cur_b:
                        cur_b.execute("SELECT * FROM buses WHERE bus_id = %s;", (req_bid,))
                        db_bus = cur_b.fetchone()
                        if db_bus:
                            chosen_bus = db_bus
                finally:
                    conn_b.close()

        # Step 2: Parse passenger details from form_data OR conversational text
        passengers_data = []
        if form_data and form_data.get("passengers"):
            passengers_data = form_data.get("passengers", [])

        if passengers_data:
            num_passengers = max(1, len(passengers_data))
            passenger_names = [p.get("name", "").strip() for p in passengers_data if p.get("name")]
            passenger_name = ", ".join(passenger_names) if passenger_names else None
            passenger_age = passengers_data[0].get("age")
            passenger_gender = passengers_data[0].get("gender", "Male")
            raw_bp = form_data.get("boarding_point")
            raw_dp = form_data.get("dropping_point")
        else:
            parsed = parse_passenger_details(user_message, source_city=source, dest_city=destination)
            num_m = re.search(r'\b(\d+)\s*(?:tickets?|passengers?|seats?|people|persons?)\b', user_message, re.IGNORECASE)
            num_passengers = int(num_m.group(1)) if num_m else 1

            passenger_name = parsed.get("name") or entities.get("passenger_name") or session.get("passenger_name")
            passenger_age = parsed.get("age") or entities.get("passenger_age") or session.get("passenger_age")
            passenger_gender = parsed.get("gender") or entities.get("passenger_gender") or session.get("passenger_gender")
            raw_bp = parsed.get("boarding") or entities.get("pickup_area") or session.get("raw_bp")
            raw_dp = parsed.get("dropping") or entities.get("drop_area") or session.get("raw_dp")

        # Retrieve available boarding and dropping points for source & destination
        src_stops = get_city_stops(source)
        all_bp_options = src_stops.get("boarding", []) or [f"{source} Central Bus Station"]
        dst_stops = get_city_stops(destination)
        all_dp_options = dst_stops.get("dropping", []) or [f"{destination} Main Bus Terminal"]

        # Step 3: Check which of the required details are missing
        if has_form_passengers:
            # Form was submitted with passenger details; ensure safe defaults so we NEVER ask twice
            if not raw_bp:
                raw_bp = all_bp_options[0]
            if not raw_dp:
                raw_dp = all_dp_options[0]
            if not passenger_gender:
                passenger_gender = "Male"
            missing_fields = []
        else:
            missing_fields = []
            if not passenger_name:
                missing_fields.append("passenger_name")
            if not passenger_age:
                missing_fields.append("passenger_age")
            if not passenger_gender:
                missing_fields.append("passenger_gender")
            if not raw_bp:
                missing_fields.append("boarding_point")
            if not raw_dp:
                missing_fields.append("dropping_point")

        if missing_fields:
            # Fetch seat availability for comfort seat selection in the form
            seats_res = tool_check_seats(chosen_bus["bus_id"])
            all_available_seats = []
            for deck in ["lower", "upper"]:
                for s in seats_res.get("decks", {}).get(deck, []):
                    if s["status"] == "available":
                        all_available_seats.append({
                            "seat_number": s["seat_number"],
                            "deck": s["deck"],
                            "type": s["type"],
                            "price": s["price"]
                        })

            # Save session for multi-turn conversational fallback
            PENDING_BOOKING_SESSIONS[user_id or 1] = {
                "source": source,
                "destination": destination,
                "date": date,
                "max_budget": budget,
                "bus_type": bus_type,
                "passenger_name": passenger_name,
                "passenger_age": passenger_age,
                "passenger_gender": passenger_gender,
                "raw_bp": raw_bp,
                "raw_dp": raw_dp,
                "bus_id": chosen_bus["bus_id"],
                "coupon_code": parsed.get("coupon") or session.get("coupon_code") or ""
            }

            # Suggest applicable promotional coupons based on trip fare
            base_fare_est = float(chosen_bus["price"])
            suggested_coupons = get_applicable_coupons(base_fare_est)

            # Format all available buses so user can pick their preferred bus in the form
            available_buses_list = []
            for b in buses_sorted[:10]:
                dep_str = b["departure_time"] if isinstance(b["departure_time"], str) else b["departure_time"].strftime("%H:%M")
                arr_str = b.get("arrival_time", "") if isinstance(b.get("arrival_time"), str) else (b["arrival_time"].strftime("%H:%M") if b.get("arrival_time") else "")
                available_buses_list.append({
                    "bus_id": b["bus_id"],
                    "bus_number": b.get("bus_number") or f"BG-{b['bus_id']:04d}",
                    "operator_name": b["operator_name"],
                    "bus_type": b["bus_type"],
                    "departure_time": dep_str,
                    "arrival_time": arr_str,
                    "price": float(b["price"]),
                    "rating": float(b.get("rating", 4.5)),
                    "available_seats": b.get("available_seats", 36)
                })

            reply_text = (
                f"I found active buses from **{source}** to **{destination}** for **{date}** "
                f"(**{chosen_bus['operator_name']}**, Bus **#{chosen_bus.get('bus_number', '')}**, ₹{chosen_bus['price']:.2f}/seat)! 🚍\n\n"
                f"Please select your preferred **bus**, filter by **price**, pick **comfort seats**, select **boarding & dropping points**, and apply a **coupon code** below:"
            )

            return {
                "success": True,
                "type": "passenger_form_needed",
                "user_message": user_message,
                "tool_called": "search_bus",
                "source": source,
                "destination": destination,
                "date": date,
                "bus_id": chosen_bus["bus_id"],
                "bus_number": chosen_bus.get("bus_number") or "",
                "bus_operator": chosen_bus["operator_name"],
                "bus_type": chosen_bus["bus_type"],
                "fare_per_seat": float(chosen_bus["price"]),
                "available_buses": available_buses_list,
                "missing_fields": missing_fields,
                "available_boarding_points": all_bp_options,
                "available_dropping_points": all_dp_options,
                "available_seats": all_available_seats,
                "decks": seats_res.get("decks", {}),
                "applicable_coupons": suggested_coupons,
                "reply": reply_text
            }

        # Step 4: All details are provided! Clear pending session and proceed to book ticket
        PENDING_BOOKING_SESSIONS.pop(user_id or 1, None)

        num_passengers = max(1, int(num_passengers or 1))

        # Match boarding & dropping points to official city stops
        boarding_point = match_stop_to_city(raw_bp, source, is_boarding=True)
        dropping_point = match_stop_to_city(raw_dp, destination, is_boarding=False)
        bus_id = chosen_bus["bus_id"]

        # Extract coupon code from form_data or conversational text
        coupon_code = ""
        if form_data and (form_data.get("coupon_code") or form_data.get("couponCode")):
            coupon_code = (form_data.get("coupon_code") or form_data.get("couponCode")).strip().upper()
        elif parsed.get("coupon"):
            coupon_code = parsed["coupon"]
        elif session.get("coupon_code"):
            coupon_code = session["coupon_code"]

        # Check if user specified preferred comfort seat numbers in form or text
        user_chosen_seats = []
        if form_data and form_data.get("passengers"):
            for p in form_data["passengers"]:
                if p.get("seat_number"):
                    user_chosen_seats.append(p["seat_number"].upper())
        elif form_data and form_data.get("selected_seats"):
            user_chosen_seats = [str(s).upper() for s in form_data["selected_seats"]]
        elif parsed.get("seat"):
            user_chosen_seats = [parsed["seat"].upper()]

        seats_res = tool_check_seats(bus_id)
        available_set = set()
        for deck in ["lower", "upper"]:
            for s in seats_res.get("decks", {}).get(deck, []):
                if s["status"] == "available":
                    available_set.add(s["seat_number"])

        allocated_seats = []
        # First allocate any valid user-selected comfort seats
        for req_s in user_chosen_seats:
            if req_s in available_set and req_s not in allocated_seats:
                allocated_seats.append(req_s)
                available_set.remove(req_s)

        # For remaining passengers, auto-assign from remaining available seats
        remaining_needed = num_passengers - len(allocated_seats)
        if remaining_needed > 0:
            for deck in ["lower", "upper"]:
                for s in seats_res.get("decks", {}).get(deck, []):
                    s_num = s["seat_number"]
                    if s_num in available_set and s_num not in allocated_seats:
                        allocated_seats.append(s_num)
                        available_set.remove(s_num)
                        if len(allocated_seats) == num_passengers:
                            break
                if len(allocated_seats) == num_passengers:
                    break

        if len(allocated_seats) < num_passengers:
            return {
                "success": False,
                "type": "booking_failed",
                "user_message": user_message,
                "tool_called": "check_seats",
                "reply": f"Sorry, only {len(allocated_seats)} seat(s) available on this bus. Please choose fewer passengers or another bus."
            }

        seat_number_str = ", ".join(allocated_seats)

        # Get user contact info
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT email, phone FROM users WHERE user_id = %s;", (user_id,))
                u_row = cursor.fetchone()
                first_name = passenger_name.split(",")[0].strip().lower().replace(" ", "")
                p_email = u_row.get("email") if u_row else f"{first_name}@busgo.com"
                p_phone = u_row.get("phone") if u_row else "9876543210"
        finally:
            conn.close()

        # Step 5: Book ticket using approved tool (with coupon discount applied)
        book_res = tool_book_ticket(
            user_id=int(user_id or 1),
            bus_id=int(bus_id),
            passenger_name=passenger_name,
            seat_number=seat_number_str,
            passenger_email=p_email,
            passenger_phone=p_phone,
            boarding_point=boarding_point,
            dropping_point=dropping_point,
            passenger_age=passenger_age,
            passenger_gender=passenger_gender,
            coupon_code=coupon_code
        )

        if not book_res.get("success"):
            return {
                "success": False,
                "type": "booking_failed",
                "user_message": user_message,
                "tool_called": "book_ticket",
                "reply": f"Sorry, could not complete booking: {book_res.get('message', 'Seat allocation failed.')}"
            }

        booking_id = book_res["booking_id"]
        pnr = book_res["pnr"]
        fare = book_res["fare"]
        dep_time = book_res["departure_time"]
        payment_url = book_res.get("payment_url", f"/payment.html?bookingId={booking_id}")

        passengers_label = f" ({num_passengers} Passenger{'s' if num_passengers > 1 else ''})" if num_passengers > 1 else f" ({passenger_gender}, {passenger_age} years)"

        fare_line = f"• **Total Fare:** **₹{fare:.2f}** (Status: **PAYMENT PENDING**)\n"
        if book_res.get("coupon_code") and book_res.get("discount", 0) > 0:
            fare_line = (
                f"• **Original Fare:** ~~₹{book_res['original_fare']:.2f}~~\n"
                f"• **Coupon Applied:** 🏷️ **`{book_res['coupon_code']}`** (-₹{book_res['discount']:.2f} savings!)\n"
                f"• **Final Payable Fare:** **₹{fare:.2f}** (Status: **PAYMENT PENDING**)\n"
            )

        bus_num = chosen_bus.get('bus_number') or book_res.get('bus_number') or ""

        reply = (
            f"🔒 **Your Bus Booking Has Been Reserved — Payment Pending**\n\n"
            f"• **PNR Number:** **`{pnr}`**\n"
            f"• **Bus Number (Vehicle No.):** 🚌 **`{bus_num}`** *(Locate this number at the bus bay / on windshield)*\n"
            f"• **Passenger(s):** **{passenger_name}**{passengers_label}\n"
            f"• **Route:** **{source}** &rarr; **{destination}**\n"
            f"• **Operator & Fleet:** **{chosen_bus['operator_name']}** ({chosen_bus['bus_type']})\n"
            f"• **Departure Date & Time:** **{date}** at **{dep_time[11:16]}**\n"
            f"• **Seat(s) Allocated:** **{seat_number_str}**\n"
            f"{fare_line}"
            f"• **Boarding Point:** 📍 **{boarding_point}**\n"
            f"• **Dropping Point:** 🏁 **{dropping_point}**\n\n"
            f"💳 **Please complete payment to confirm and print your ticket.**\n"
            f"⏰ *Your seat(s) are held for 10 minutes. Click below to proceed to payment:*\n"
            f"👉 [**Proceed to Payment →**]({payment_url})"
        )

        return {
            "success": True,
            "type": "ticket_booked",
            "user_message": user_message,
            "tool_called": "book_ticket",
            "reply": reply,
            "booking": {
                "booking_id": booking_id,
                "pnr": pnr,
                "bus_number": bus_num,
                "passenger_name": passenger_name,
                "passenger_age": passenger_age,
                "passenger_gender": passenger_gender,
                "num_passengers": num_passengers,
                "source": source,
                "destination": destination,
                "bus_operator": chosen_bus['operator_name'],
                "bus_type": chosen_bus['bus_type'],
                "departure_time": dep_time,
                "seat_number": seat_number_str,
                "original_fare": book_res.get("original_fare", fare),
                "discount": book_res.get("discount", 0.0),
                "coupon_code": book_res.get("coupon_code"),
                "fare": fare,
                "boarding_point": boarding_point,
                "dropping_point": dropping_point,
                "status": "PENDING",
                "payment_status": "PENDING",
                "payment_url": payment_url
            }
        }

    # 4. Standard Bus Search (Module 3 & FR-05)
    source = entities.get("source")
    destination = entities.get("destination")

    # If missing origin/destination, ask conversational clarification
    if not source or not destination:
        return {
            "success": True,
            "type": "clarification_needed",
            "user_message": user_message,
            "tool_called": None,
            "reply": (
                "To search for buses, please specify your **Origin City** and **Destination City** "
                "(for example: *'Find a sleeper bus from Hyderabad to Bangalore on 20 November'*)."
            )
        }

    search_res = tool_search_bus(
        source=source,
        destination=destination,
        date=entities.get("date"),
        bus_type=entities.get("bus_type"),
        max_price=entities.get("max_budget")
    )

    buses = search_res.get("buses", [])
    count = len(buses)

    if count == 0:
        dt_str = f" on {entities['date']}" if entities.get("date") else ""
        bg_str = f" under ₹{entities['max_budget']}" if entities.get("max_budget") else ""
        reply = (
            f"No buses currently matched your criteria from **{source}** to **{destination}**"
            f"{dt_str}{bg_str}. "
            f"Try removing the price budget filter or checking an alternate date."
        )
    else:
        bus_type_str = f" {entities['bus_type']}" if entities.get("bus_type") else ""
        budget_str = f" under ₹{entities['max_budget']:.0f}" if entities.get("max_budget") else ""
        date_str = f" for **{entities['date']}**" if entities.get("date") else ""
        
        pickup_info = f"\n• **Preferred Pickup Point:** **{entities['pickup_area']}** ({source})" if entities.get("pickup_area") else ""
        drop_info = f"\n• **Preferred Dropping Point:** **{entities['drop_area']}** ({destination})" if entities.get("drop_area") else ""
        budget_info = f"\n• **Budget Limit:** ₹{entities['max_budget']:.0f}" if entities.get("max_budget") else ""

        pref_header = ""
        if pickup_info or drop_info or budget_info:
            pref_header = f"\n**Trip Preferences Identified:**{pickup_info}{drop_info}{budget_info}\n"

        options_list = "\n".join([
            f"{i+1}. **{b['operator_name']}** ({b['bus_type']}) – **₹{b['price']:.2f}** | Departs: {b['departure_time'][11:16]} | ⭐ {b['rating']}"
            for i, b in enumerate(buses[:4])
        ])

        reply = (
            f"I found **{count} matching{bus_type_str} bus option{'s' if count > 1 else ''}** from **{source}** to **{destination}**{date_str}{budget_str}:{pref_header}\n"
            f"**Recommended Buses:**\n{options_list}\n\n"
            f"*(Note: Pickup at **{entities.get('pickup_area', source + ' Central')}** and Drop at **{entities.get('drop_area', destination + ' Main')}** will be reserved with your selected bus).* "
        )

    return {
        "success": True,
        "type": "bus_search",
        "user_message": user_message,
        "tool_called": "search_bus",
        "reply": reply,
        "criteria": entities,
        "buses": buses
    }


if __name__ == "__main__":
    print("[*] Testing Agent Natural Language Travel Search:")
    res = process_agent_request("Find a sleeper bus from Hyderabad to Bangalore on 20 November within a budget of 1000 rupees.")
    print("Tool Called:", res.get("tool_called"))
    print("Reply:", res.get("reply"))
    print("Buses Returned:", len(res.get("buses", [])))
