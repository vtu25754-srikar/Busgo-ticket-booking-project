"""
BUSGO Playwright Browser Automation Service
Implements SRS Module 8 & FR-14:
- Permitted browser interaction using Playwright Chromium
- Automated bus search navigation
- Automated seat inspection workflow
- Captures execution logs, step metrics, and screenshots
"""

import os
import base64
import time
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "automation_snapshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def run_automated_bus_search(
    from_city: str = "Hyderabad",
    to_city: str = "Bangalore",
    travel_date: str = "2026-11-20",
    base_url: str = "http://localhost:5000",
    headless: bool = True
) -> Dict[str, Any]:
    """
    Automates permitted bus search navigation using Playwright.
    Enters travel search details, inspects matching buses, and takes a snapshot.
    """
    logs: List[str] = []
    snapshot_path = os.path.join(SCREENSHOT_DIR, f"search_{from_city}_{to_city}.png")
    
    start_time = time.time()
    logs.append(f"[{time.strftime('%H:%M:%S')}] Initializing Playwright Automation Engine...")

    try:
        with sync_playwright() as p:
            logs.append(f"[{time.strftime('%H:%M:%S')}] Launching Chromium (Headless: {headless})...")
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})

            target_url = f"{base_url}/search.html?from={from_city}&to={to_city}&date={travel_date}"
            logs.append(f"[{time.strftime('%H:%M:%S')}] Navigating to BUSGO search portal: {target_url}")
            
            page.goto(target_url, timeout=15000, wait_until="networkidle")
            time.sleep(1)

            logs.append(f"[{time.strftime('%H:%M:%S')}] Inspecting DOM elements for bus listings...")
            
            # Extract bus cards
            bus_cards = page.query_selector_all(".bus-card")
            extracted_buses = []
            
            for card in bus_cards[:5]:
                op_elem = card.query_selector(".bus-operator")
                price_elem = card.query_selector(".price-value")
                type_elem = card.query_selector(".bus-type")
                time_elem = card.query_selector(".departure-time")
                
                extracted_buses.append({
                    "operator": op_elem.inner_text().strip() if op_elem else "Bus Operator",
                    "price": price_elem.inner_text().strip() if price_elem else "N/A",
                    "type": type_elem.inner_text().strip() if type_elem else "Sleeper",
                    "time": time_elem.inner_text().strip() if time_elem else "N/A"
                })

            logs.append(f"[{time.strftime('%H:%M:%S')}] Extracted {len(extracted_buses)} bus options from page.")
            
            # Save screenshot
            page.screenshot(path=snapshot_path)
            logs.append(f"[{time.strftime('%H:%M:%S')}] Page snapshot captured successfully.")

            # Base64 encode screenshot for direct UI presentation
            with open(snapshot_path, "rb") as img_f:
                screenshot_base64 = base64.b64encode(img_f.read()).decode("utf-8")

            browser.close()
            elapsed = round(time.time() - start_time, 2)
            logs.append(f"[{time.strftime('%H:%M:%S')}] Automation task finished in {elapsed}s.")

            return {
                "success": True,
                "workflow": "automated_bus_search",
                "from_city": from_city,
                "to_city": to_city,
                "travel_date": travel_date,
                "duration_seconds": elapsed,
                "buses_found": extracted_buses,
                "logs": logs,
                "screenshot_base64": f"data:image/png;base64,{screenshot_base64}"
            }

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logs.append(f"[{time.strftime('%H:%M:%S')}] Automation Error: {str(e)}")
        return {
            "success": False,
            "workflow": "automated_bus_search",
            "error": str(e),
            "logs": logs,
            "duration_seconds": elapsed
        }


def run_automated_seat_workflow(
    bus_id: int = 1,
    base_url: str = "http://localhost:5000",
    headless: bool = True
) -> Dict[str, Any]:
    """
    Automates opening seat selector, inspecting berths, and selecting an available seat.
    """
    logs: List[str] = []
    snapshot_path = os.path.join(SCREENSHOT_DIR, f"seats_bus_{bus_id}.png")
    start_time = time.time()
    logs.append(f"[{time.strftime('%H:%M:%S')}] Starting Automated Seat Selection Workflow for Bus #{bus_id}...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})

            target_url = f"{base_url}/seats.html?scheduleId={bus_id}"
            logs.append(f"[{time.strftime('%H:%M:%S')}] Loading interactive seat map at: {target_url}")
            page.goto(target_url, timeout=15000, wait_until="networkidle")
            time.sleep(1)

            # Inspect available seats
            available_seats = page.query_selector_all(".seat-berth:not(.booked)")
            logs.append(f"[{time.strftime('%H:%M:%S')}] Detected {len(available_seats)} available berths on deck.")

            selected_seat_text = "N/A"
            if available_seats:
                first_seat = available_seats[0]
                first_seat.click()
                selected_seat_text = first_seat.get_attribute("data-seat-id") or first_seat.inner_text().strip()
                logs.append(f"[{time.strftime('%H:%M:%S')}] Automated user action: clicked berth '{selected_seat_text}'.")
                time.sleep(0.5)

            page.screenshot(path=snapshot_path)
            logs.append(f"[{time.strftime('%H:%M:%S')}] Seat selection snapshot saved.")

            with open(snapshot_path, "rb") as img_f:
                screenshot_base64 = base64.b64encode(img_f.read()).decode("utf-8")

            browser.close()
            elapsed = round(time.time() - start_time, 2)
            logs.append(f"[{time.strftime('%H:%M:%S')}] Seat automation completed in {elapsed}s.")

            return {
                "success": True,
                "workflow": "automated_seat_selection",
                "bus_id": bus_id,
                "selected_seat": selected_seat_text,
                "duration_seconds": elapsed,
                "logs": logs,
                "screenshot_base64": f"data:image/png;base64,{screenshot_base64}"
            }

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logs.append(f"[{time.strftime('%H:%M:%S')}] Seat Automation Error: {str(e)}")
        return {
            "success": False,
            "workflow": "automated_seat_selection",
            "error": str(e),
            "logs": logs,
            "duration_seconds": elapsed
        }


if __name__ == "__main__":
    print("[*] Playwright Automation Service ready.")
