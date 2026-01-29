import argparse
from datetime import date
import json
import os
import re
import uuid
from aiohttp import web
from duffel_client import DuffelClient

from dotenv import load_dotenv
load_dotenv()

DEFAULT_PORT = int(os.getenv("AMADEUS_AGENT_PORT", os.getenv("PORT", "10103")))
DEFAULT_HOST = os.getenv("AMADEUS_AGENT_HOST", os.getenv("HOST", "0.0.0.0"))


def parse_query(text: str):
    """
    Supports: "San Francisco to London, Jan 20-27, 2026, economy flight"
    """
    q = text.lower()

    # Very basic city → IATA mapping (you can expand later)
    city_to_iata = {
    # USA
        "san francisco": "SFO",
        "new york": "NYC",
        "los angeles": "LAX",
        "chicago": "CHI",
        "washington": "WAS",
        "miami": "MIA",
        "dallas": "DFW",
        "seattle": "SEA",
        "boston": "BOS",
        "las vegas": "LAS",

        # UK
        "london": "LON",
        "manchester": "MAN",
        "edinburgh": "EDI",

        # France
        "paris": "PAR",
        "nice": "NCE",

        # India
        "chennai": "MAA",
        "delhi": "DEL",
        "mumbai": "BOM",
        "bengaluru": "BLR",
        "bangalore": "BLR",
        "hyderabad": "HYD",
        "kolkata": "CCU",
        "kochi": "COK",
        "cochin": "COK",
        "trivandrum": "TRV",
        "thiruvananthapuram": "TRV",
        "pune": "PNQ",
        "ahmedabad": "AMD",
        "jaipur": "JAI",
        "goa": "GOI",
        "lucknow": "LKO",
        "coimbatore": "CJB",
        "madurai": "IXM",
        "visakhapatnam": "VTZ",

        # Singapore / UAE
        "singapore": "SIN",
        "dubai": "DXB",
        "abu dhabi": "AUH",

        # Qatar / Saudi
        "doha": "DOH",
        "riyadh": "RUH",
        "jeddah": "JED",

        # Thailand / Malaysia / Indonesia
        "bangkok": "BKK",
        "phuket": "HKT",
        "kuala lumpur": "KUL",
        "jakarta": "JKT",
        "bali": "DPS",

        # Japan / South Korea / China
        "tokyo": "TYO",
        "osaka": "OSA",
        "seoul": "SEL",
        "beijing": "BJS",
        "shanghai": "SHA",
        "hong kong": "HKG",

        # Australia / New Zealand
        "sydney": "SYD",
        "melbourne": "MEL",
        "brisbane": "BNE",
        "auckland": "AKL",

        # Europe
        "rome": "ROM",
        "milan": "MIL",
        "amsterdam": "AMS",
        "berlin": "BER",
        "munich": "MUC",
        "frankfurt": "FRA",
        "zurich": "ZRH",
        "vienna": "VIE",
        "madrid": "MAD",
        "barcelona": "BCN",

        # Canada
        "toronto": "YTO",
        "vancouver": "YVR",
        "montreal": "YMQ",

        "colombo": "CMB",
    }


    origin = None
    destination = None

    # Try to detect "X to Y"
    m = re.search(r"(.+?)\s+to\s+(.+?)(?:,|$)", q)
    if m:
        from_city = m.group(1).strip()
        to_city = m.group(2).strip()

        for city, code in city_to_iata.items():
            if city in from_city:
                origin = code
            if city in to_city:
                destination = code

    # Dates: Jan 20-27, 2026
    date_match = re.search(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})-(\d{1,2}),\s*(\d{4})",
    q
    )

    dep_date = None
    ret_date = None

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }

    if date_match:
        mon, d1, d2, year = date_match.groups()
        mm = month_map[mon]
        dep_date = f"{year}-{mm}-{d1.zfill(2)}"
        ret_date = f"{year}-{mm}-{d2.zfill(2)}"

    # Class
    travel_class = "ECONOMY"
    if "business" in q:
        travel_class = "BUSINESS"
    elif "first" in q:
        travel_class = "FIRST"

    return origin, destination, dep_date, ret_date, travel_class


def normalize_flights(api_json):
    """Convert Duffel offer request response into a simple flights list.

    We expect a structure like:
      {"data": {"offers": [ {"id": ..., "total_amount": ..., "total_currency": ..., "owner": {...}, "slices": [...]}, ... ]}}
    """
    flights: list[dict] = []

    data = api_json.get("data") or {}
    offers = data.get("offers") or []

    for offer in offers[:8]:
        slices = offer.get("slices") or []
        if not slices:
            continue

        # Use the first slice as the "outbound" for display
        first_slice = slices[0]
        segments = first_slice.get("segments") or []
        if not segments:
            continue

        first_seg = segments[0]
        last_seg = segments[-1]

        owner = offer.get("owner") or {}
        price = {
            "total": offer.get("total_amount"),
            "currency": offer.get("total_currency"),
        }

        # departure/arrival timestamps are usually `departing_at` / `arriving_at`
        departure = first_seg.get("departing_at") or first_seg.get("departure_time")
        arrival = last_seg.get("arriving_at") or last_seg.get("arrival_time")

        flights.append({
            "airline": owner.get("name") or owner.get("iata_code") or "N/A",
            "departure": departure,
            "arrival": arrival,
            "stops": max(len(segments) - 1, 0),
            "total_price": price.get("total"),
            "currency": price.get("currency"),
            "offer_id": offer.get("id"),
        })

    return flights


async def handle(request: web.Request):
    payload = await request.json()

    # A2A style message text
    text = payload["params"]["message"]["parts"][0]["text"]
    req_id = payload.get("id", "1")
    task_id = str(uuid.uuid4())

    origin, destination, dep, ret, travel_class = parse_query(text)

    # Guardrails: avoid calling external APIs with obviously invalid dates.
    # (Amadeus sandbox can return a generic 500/system error for these.)
    if dep:
        try:
            dep_d = date.fromisoformat(dep)
            if dep_d < date.today():
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "kind": "artifact-update",
                        "artifact": {"parts": [{"data": []}]},
                        "taskId": task_id
                    }
                })
        except ValueError:
            dep = None

    if ret and dep:
        try:
            if date.fromisoformat(ret) <= date.fromisoformat(dep):
                ret = None
        except ValueError:
            ret = None

    # If missing critical info, return empty list (no chatting)
    if not origin or not destination or not dep:
        return web.json_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "kind": "artifact-update",
                "artifact": {"parts": [{"data": []}]},
                "taskId": task_id
            }
        })

    try:
        client = DuffelClient()

        # Map internal travel_class to Duffel cabin_class
        cabin_map = {
            "ECONOMY": "economy",
            "BUSINESS": "business",
            "FIRST": "first",
        }
        cabin_class = cabin_map.get(travel_class.upper(), "economy") if travel_class else "economy"

        # Use city codes (NYC, ATL) or airport codes (JFK, LHR, MAA, etc.)
        data = await client.search_offers(
            origin=origin,
            destination=destination,
            departure_date=dep,
            return_date=ret,
            cabin_class=cabin_class,
        )

        flights = normalize_flights(data)

    except Exception as e:
        # return empty list on error
        flights = []
        print("ERROR:", str(e))

    return web.json_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "kind": "artifact-update",
            "artifact": {
                "parts": [{"data": flights}]
            },
            "taskId": task_id
        }
    })


app = web.Application()
app.router.add_post("/", handle)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Amadeus flight-offers A2A-compatible agent")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    web.run_app(app, host=args.host, port=args.port)
