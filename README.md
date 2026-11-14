# 🚌 BUSGO: Agentic AI-Based Intelligent Bus Ticket Booking & Travel Assistance System Using Claude and RAG

> **Domain:** Travel & Transportation  
> **Target Platform:** Full-Stack Responsive Web Application (Inspired by RedBus)  
> **Core Technologies:** Python Flask, MySQL, ChromaDB, Anthropic Claude AI, Playwright Web Automation

---

## 📌 1. Project Overview

**BUSGO** is an intelligent, agentic AI-powered bus ticket booking assistance application developed strictly according to the Software Requirements Specification (SRS). 

Users can describe complex travel requirements in conversational natural language (e.g., *"Find a sleeper bus from Hyderabad to Bangalore on 20 November within a budget of 1,000 rupees"*). The system interprets the intent, extracts entities, executes approved backend tools, queries an embedded RAG knowledge base for cancellation and luggage policies, compares options, provides interactive seat selection, and demonstrates permitted browser automation using Playwright.

---

## 🛠️ 2. Technology Stack

| Component | Technology | Role in System |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | RedBus-inspired responsive UI, interactive deck seat selector, floating AI assistant drawer |
| **Backend** | Python 3.14 + Flask + Flask-CORS | REST APIs, agent tool executor, business logic, static asset server |
| **Database** | MySQL 8.x (`busgo_db`) | Structured application data across 5 SRS relational tables |
| **Generative AI** | Anthropic Claude API (`anthropic` SDK) | Natural language understanding, intent extraction, grounded answer synthesis |
| **RAG Component** | ChromaDB (Vector Database) + ONNX MiniLM | Semantic storage and retrieval of travel policy & FAQ document chunks |
| **Web Automation** | Playwright Chromium | Permitted browser automation for search navigation and seat inspection |
| **Testing** | Python `unittest` | Complete 14-test verification suite covering TC-01 through TC-14 |

---

## 🏛️ 3. System Architecture & Layers

```text
       USER / WEB BROWSER
              │
              ▼
  HTML5 / CSS3 / JavaScript
 (RedBus-Style Web Application)
              │
              ▼
    PYTHON FLASK BACKEND
   ┌──────────┼──────────┐
   │          │          │
   ▼          ▼          ▼
MYSQL DB   CLAUDE AI  PLAYWRIGHT
(busgo_db) (Anthropic) (Automation)
   │          │
   │   ┌──────┴──────┐
   │   ▼             ▼
   │  RAG        AI AGENT
   │ (ChromaDB) (Approved Tools)
   │   │             │
   │   ▼             ▼
 TRAVEL DOCS   search_bus / compare_bus /
 (Policies/FAQ) check_seats / book_ticket
```

---

## 📦 4. SRS Modules Implemented

- **Module 1: User Management (FR-01, FR-02)** – User registration, secure SHA-256 password hashing, token-based session login, profile management.
- **Module 2: AI Travel Assistant (FR-03, FR-04)** – Conversational interface extracting origin, destination, date, bus type (AC/Non-AC Sleeper/Seater), and budget from free-form natural language.
- **Module 3: Bus Search & Comparison (FR-05, FR-06)** – Real-time route searching, multi-criteria filtering, and price/rating sorting across major operators (Orange Travels, VRL, IntrCity SmartBus, Zingbus, SRS Travels).
- **Module 4: RAG-Based Knowledge Assistant (FR-10)** – ChromaDB semantic vector retrieval on 5 verified travel documents (Cancellation & Refund, Booking FAQs, Luggage Allowance, Deck Guide, Passenger Guidelines). Accurately indicates unavailability when queries are unsupported (TC-07).
- **Module 5: AI Agent & Tool Calling (FR-11)** – Backend execution of approved tools (`search_bus()`, `compare_bus()`, `check_seats()`, `get_booking_history()`, `search_travel_policy()`, `book_ticket()`, `cancel_booking()`).
- **Module 6: Interactive Seat Selection (FR-07, FR-08)** – RedBus-style Lower and Upper deck layouts, berth categories, single ladies seat reservation protection.
- **Module 7: Booking Management (FR-09, FR-12, FR-13)** – Passenger details collection, unique PNR generation, cancellation refund computation (>72h: 90%, 24-72h: 50%, <24h: 0%), printable electronic ticket.
- **Module 8: Browser Automation (FR-14)** – Headless Chromium automation using Playwright with DOM inspection, step logging, and live snapshot capture.

---

## 🗄️ 5. Database Design (SRS Section 9)

The MySQL database `busgo_db` contains the 5 primary tables specified in the SRS:

1. **`users`** – `user_id` (PK), `username`, `email`, `password_hash`, `phone`, `role`, `created_at`.
2. **`buses`** – `bus_id` (PK), `operator_name`, `source`, `destination`, `departure_time`, `arrival_time`, `bus_type`, `price`, `available_seats`, `total_seats`, `facilities`, `rating`.
3. **`bookings`** – `booking_id` (PK), `user_id` (FK), `bus_id` (FK), `passenger_name`, `seat_number`, `booking_date`, `booking_status`, `total_fare`, `pnr_number`, `payment_status`.
4. **`chat_history`** – `chat_id` (PK), `user_id` (FK), `user_message`, `ai_response`, `tool_called`, `created_at`.
5. **`travel_knowledge`** – `document_id` (PK), `document_name`, `document_type`, `content_preview`, `upload_date`.
6. **`seat_reservations`** – Tracks individual deck berth statuses (L1–L18, U1–U18) and female-only seat flags.

---

## 🚀 6. Setup & Running Instructions

### Prerequisites
- **Python 3.10+** (Python 3.14 verified)
- **MySQL 8.x** running on `localhost:3306` with user `root` (password configurable in `backend/.env` or `backend/init_db.py`).

### 1. Database Initialization & Seeding
From the project root:
```bash
python backend/init_db.py
```
*Creates `busgo_db`, all relational tables, default users, 210 bus schedules across 15 travel dates, and document metadata.*

### 2. Start the Application Server
Run using **npm**:
```bash
npm run dev
```
*(Alternatively, you can also run `npm start` or `python backend/app.py`)*

### 3. Additional NPM Scripts
- `npm run dev` – Launch Flask web server & frontend on port 5000
- `npm test` – Execute full 14-test SRS verification suite
- `npm run seed` – Populate expanded bus fleet (6,240 schedules across 208 routes)
- `npm run init-db` – Recreate database schema and seed knowledge base documents

You will see:
```text
============================================================
🚌 BUSGO Agentic AI Travel System Server
Backend: Python Flask | Generative AI: Claude & RAG
Database: MySQL (busgo_db) | Vector Store: ChromaDB
============================================================
[*] Initializing MySQL database 'busgo_db' on localhost:3306...
[+] Database tables successfully created.
[*] Initializing RAG Knowledge Base from: .../backend/knowledge_base
[+] ChromaDB collection 'busgo_travel_docs' populated with 5 chunks.

🌍 Web Server live at: http://localhost:5000
```

### 3. Open the Web Application
Open your browser and navigate to:
👉 **`http://localhost:5000`**

### Available Pages:
- **Home & Hero Search:** `http://localhost:5000/index.html`
- **🤖 AI Travel Assistant & Demonstration Hub:** `http://localhost:5000/ai-assistant.html`
- **Live Bus Search Results:** `http://localhost:5000/search.html?from=Hyderabad&to=Bangalore`
- **Interactive Deck Seat Selector:** `http://localhost:5000/seats.html?scheduleId=1`
- **Customer My Bookings & Cancellation:** `http://localhost:5000/mybookings.html`
- **Customer Login:** `http://localhost:5000/login.html`

---

## 🎯 7. Three Working Demonstrations (SRS Section 16 - HCLTech Evaluation)

Open `http://localhost:5000/ai-assistant.html` to run each live demonstration with a single click:

| Demo | Title | What it Evaluates |
|---|---|---|
| **Demo 1** | **Natural-Language Bus Search & Comparison** | Prompts: *"Find the cheapest sleeper bus from Hyderabad to Bangalore and compare options."* Validates Claude entity extraction and execution of `compare_bus()`. |
| **Demo 2** | **Cancellation & Refund Question via RAG** | Prompts: *"What is the refund percentage if I cancel my ticket 30 hours before travel?"* Demonstrates ChromaDB semantic retrieval returning verified 50% refund slab without hallucination. |
| **Demo 3** | **Multi-Step AI Agent Tool Execution** | AI Agent coordinates 3 approved tools in sequence: `search_bus()` &rarr; `check_seats()` &rarr; `book_ticket()` to complete booking and generate a confirmed PNR. |

---

## 🗺️ 8. South India Predefined Bus Routes & Dynamic Boarding/Dropping Points

The project contains a normalized database of **30 major South Indian intercity corridors** across Telangana (TS), Andhra Pradesh (AP), Tamil Nadu (TN), Karnataka (KA), and Kerala (KL) with **135 exact boarding and 135 exact dropping points**:

- **Hub Cities:** Hyderabad (20 points), Chennai (25 points), Bangalore (25 points), Vijayawada (15 points), Tirupati (10 points), Visakhapatnam (10 points), Coimbatore (10 points), Madurai (10 points), plus Kurnool, Kochi, and Mysore.
- **Relational Tables:** `cities`, `routes`, `boarding_points`, `dropping_points`, `bus_operators`, `route_operators`.
- **Active Schedules:** 4,680 real schedules populated across low-cost budget to luxury AC sleepers for the next 30 days.
- **Interactive Route Map:** Powered by Leaflet/OpenStreetMap on `seats.html`, showing pickup marker (🟢), drop marker (🔴), distance calculation in km, and route polyline that updates dynamically as the user changes boarding or dropping locations.
- **Claude AI NLP Specific Query:** Handles specific queries like *"I want to travel from Chennai to Bangalore tomorrow. Pick me up near Ambattur and drop me near Electronic City. My budget is ₹800."* — extracting Ambattur as pickup, Electronic City as drop, budget ₹800, and matching buses strictly under budget without altering user pickup/drop preferences.

---

## 💳 9. Two-Phase Payment Gateway & Ticket Auto-Print

Implemented on `frontend/payment.html` with multi-mode checkout (UPI/QR, Credit/Debit Card, Net Banking, Wallets):
1. **Phase 1: 20-Second Security Authorization Timer**
   - Active circular timer and progress bar counting down from 20 to 0 seconds.
   - The **Verify Payment** button remains disabled during the 20-second security window.
   - Once the 20 seconds elapse, the button unlocks with green active styling: `✓ Verify Payment & Proceed`.
   - Includes a *Fast-Forward 20s (Demo Mode)* shortcut for quick testing during demonstrations.
2. **Phase 2: 5-Second Verification & Auto-Print**
   - On clicking the unlocked Verify button, the modal switches to a 5-second countdown timer (5, 4, 3, 2, 1, 0).
   - Authorizes the transaction with `/api/payments/verify`.
   - At 0 seconds, triggers an automatic popup/window to print/download the official electronic ticket (`/api/bookings/<id>/download-ticket`) and redirects to `confirmation.html`.

---

## 🧪 10. Automated Test Suite (SRS Section 12)

Run the complete automated test suite:
```bash
python backend/test_system.py
# or
npm test
```

Output:
```text
..............
----------------------------------------------------------------------
Ran 14 tests in 47.261s

OK
```
Covers:
- `TC-01`: User Registration
- `TC-02`: User Login
- `TC-03`: Bus Search (valid criteria)
- `TC-04`: Invalid Search Input validation
- `TC-05`: Price Comparison & sorting
- `TC-06`: RAG Question answering
- `TC-07`: Unsupported RAG Question handling (no hallucination)
- `TC-08`: AI Agent Tool Calling
- `TC-09`: Seat Selection & deck layout inspection
- `TC-10`: User Booking History retrieval
- `TC-11`: Claude API reliability & fallback
- `TC-12`: Booking Confirmation & PNR generation
- `TC-13`: HCLTech 3 Working Demonstrations endpoints
- `TC-14`: Playwright Browser Automation execution & snapshot capture
