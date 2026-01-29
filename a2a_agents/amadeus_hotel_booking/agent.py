import json
import re
import uuid
import os
import time
import httpx
from aiohttp import web
from dotenv import load_dotenv
from amadeus_client import AmadeusClient

load_dotenv()

PORT = 10104

# Set `A2A_DEBUG=1` in environment to enable verbose logs.
DEBUG = os.getenv("A2A_DEBUG", "").strip() not in ("", "0", "false", "False")

# Default hotel image - using a reliable public image URL
DEFAULT_HOTEL_IMAGE = "0"

# Max number of hotel cards to return to the UI.
MAX_HOTELS = 8

# Keep the hotel agent responsive: the A2UI orchestrator uses a 60s timeout.
# We aim to respond well under that by limiting slow enrichment.
TOTAL_TIME_BUDGET_SECONDS = 45.0
SERPAPI_MAX_LOOKUPS = 2
SERPAPI_TIMEOUT_SECONDS = 6.0


def _dlog(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def parse_hotel_query(text: str):
    """
    Supports queries like:
    1) "London, Jan 20-27, 2026, hotel 2 guests"
    2) "Chennai to Delhi, Mar 5-10, 2026, economy flight and hotel 1 guests"
       -> Hotel will be searched in destination city (Delhi)
    """
    q = text.lower()

    # Simple city -> cityCode mapping (Amadeus uses IATA city codes)
    city_to_code = {
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

    city_code = None

    # ✅ Prefer destination city after "to"
    m = re.search(r"\bto\s+([a-z\s]+?)(?:,|$)", q)
    if m:
        dest_city = m.group(1).strip()
        for city, code in city_to_code.items():
            if city in dest_city:
                city_code = code
                break

    # fallback: first city found anywhere in query
    if not city_code:
        for city, code in city_to_code.items():
            if city in q:
                city_code = code
                break

    # Dates: Jan 20-27, 2026 OR Mar 5-10, 2026
    date_match = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})-(\d{1,2}),\s*(\d{4})",
        q
    )

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }

    checkin = None
    checkout = None

    if date_match:
        mon, d1, d2, year = date_match.groups()
        mm = month_map[mon]
        checkin = f"{year}-{mm}-{d1.zfill(2)}"
        checkout = f"{year}-{mm}-{d2.zfill(2)}"

    # Guests
    guests = 1
    guests_match = re.search(r"(\d+)\s*guests?", q)
    if guests_match:
        guests = int(guests_match.group(1))

    return city_code, checkin, checkout, guests


def first_image_url(hotel: dict) -> str:
    """
    Returns the first HTTPS image URL or a fallback placeholder.
    """
    # Try different possible locations for media in Amadeus response
    media = hotel.get("media", [])
    if not media:
        media = hotel.get("hotelMedia", [])
    
    for item in media:
        if isinstance(item, dict):
            url = item.get("uri", "")
        else:
            url = str(item)
            
        if url and url.startswith("http"):
            return url
    
    # No image found in Amadeus payload
    return ""

async def fetch_image_with_serpapi(query: str) -> str:
    """Fetch a hotel image via SerpAPI (Google Images). Returns empty string if not available."""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key or not query:
        return ""

    params = {
        "engine": "google_images",
        "q": query,
        "api_key": api_key,
        "ijn": "0",
        "safe": "active",
    }

    try:
        async with httpx.AsyncClient(timeout=SERPAPI_TIMEOUT_SECONDS) as client:
            r = await client.get("https://serpapi.com/search.json", params=params)
        if r.status_code != 200:
            return ""
        data = r.json()
        images = data.get("images_results", [])

        def _looks_like_a_real_photo(url: str, title: str = "") -> bool:
            if not url or not url.startswith("http"):
                return False
            u = url.lower()
            t = (title or "").lower()
            # Avoid maps, logos, icons, vectors, and similar non-photo assets.
            bad_tokens = [
                "map",
                "maps",
                "logo",
                "icon",
                "svg",
                "vector",
                "floorplan",
                "site:",
            ]
            if any(tok in u for tok in bad_tokens) or any(tok in t for tok in bad_tokens):
                return False
            # Avoid obvious blog/map pages that frequently rank for "hotel maps".
            bad_domains = [
                "santorinidave.com",
                "pinterest.",
            ]
            if any(d in u for d in bad_domains):
                return False
            # Prefer common image formats.
            if any(u.endswith(ext) for ext in (".svg", ".pdf")):
                return False
            return True

        for img in images:
            # Prefer the original image URL when available
            url = img.get("original") or img.get("thumbnail") or img.get("link")
            title = img.get("title") or img.get("snippet") or ""
            if _looks_like_a_real_photo(url, title=title):
                return url
    except Exception:
        return ""

    return ""


async def normalize_hotels(amadeus_json, city_code: str, ctx: dict | None = None):
    """
    Extract hotel name + price info from Amadeus response, with image URL.
    Falls back to SerpAPI if Amadeus media is missing, then to city-specific defaults.
    """
    results = []

    ctx = ctx or {}
    deadline = float(ctx.get("deadline", float("inf")))
    serpapi_remaining = int(ctx.get("serpapi_remaining", SERPAPI_MAX_LOOKUPS))

    for item in amadeus_json.get("data", [])[:MAX_HOTELS]:
        hotel = item.get("hotel", {})
        offers = item.get("offers", [])

        if not offers:
            continue

        offer = offers[0]
        price = offer.get("price", {})

        # Debug: print hotel data to see structure
        _dlog(f"Hotel data keys: {hotel.keys()}")
        if "media" in hotel:
            _dlog(f"Media found: {hotel['media']}")

        # Get image from Amadeus first
        img_url = first_image_url(hotel)
        
        # Skip SerpAPI for test/demo properties - they return irrelevant images
        if not img_url:
            hotel_name = hotel.get("name", "")
            hotel_name_lower = hotel_name.lower()
            # Only use SerpAPI for real hotel names (not test data)
            is_test_property = any(keyword in hotel_name_lower for keyword in ["test", "demo", "api activate", "migration", "uat", "sample"])
            
            # Only do a small number of SerpAPI lookups and only if we still have time.
            has_time = time.monotonic() < (deadline - 2.0)
            if not is_test_property and hotel_name and serpapi_remaining > 0 and has_time:
                # Add context + negative keywords to avoid "maps" and "logos".
                query = f'"{hotel_name}" {city_code} hotel photo -map -maps -logo'
                img_url = await fetch_image_with_serpapi(query)
                serpapi_remaining -= 1
                _dlog(f"SerpAPI searched for: {query}, found: {img_url[:80] if img_url else 'None'}")
            else:
                _dlog(f"Skipped SerpAPI for test property: {hotel_name}")
        
        # Use default image if nothing found
        if not img_url:
            img_url = DEFAULT_HOTEL_IMAGE
        
        # Ensure we always have a valid URL
        if not img_url or not (img_url.startswith("http://") or img_url.startswith("https://") or img_url.startswith("data:")):
            img_url = DEFAULT_HOTEL_IMAGE

        results.append({
            "name": hotel.get("name"),
            "hotel_id": hotel.get("hotelId"),
            "check_in": offer.get("checkInDate"),
            "check_out": offer.get("checkOutDate"),
            "price": f"{price.get('total')} {price.get('currency')}",
            "rating": hotel.get("rating", "N/A"),
            "room_type": offer.get("room", {}).get("typeEstimated", {}).get("category", "N/A"),
            "imageUrl": img_url
        })

    return results


async def handle(request: web.Request):
    payload = await request.json()
    text = payload["params"]["message"]["parts"][0]["text"]

    req_id = payload.get("id", "1")
    task_id = str(uuid.uuid4())

    city_code, checkin, checkout, guests = parse_hotel_query(text)

    # Debug prints (optional)
    _dlog("QUERY:", text)
    _dlog("PARSED:", city_code, checkin, checkout, guests)

    if not city_code or not checkin or not checkout:
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
        deadline = time.monotonic() + TOTAL_TIME_BUDGET_SECONDS
        ctx = {"deadline": deadline, "serpapi_remaining": SERPAPI_MAX_LOOKUPS}
        amadeus = AmadeusClient()

        # 1) Get hotel IDs in the city
        hotels_list = await amadeus.get(
            "/v1/reference-data/locations/hotels/by-city",
            params={
                "cityCode": city_code,
                "radius": 10,
                "radiusUnit": "KM"
            }
        )

        # Log full response for debugging
        _dlog("hotels_list response:", json.dumps(hotels_list, indent=2)[:1000])

        # Pull more hotelIds; many will have 0 availability in TEST.
        hotel_ids = [h["hotelId"] for h in hotels_list.get("data", [])[:25]]
        _dlog("Hotel IDs:", hotel_ids)

        if not hotel_ids:
            _dlog("No hotel IDs found. Full response:", json.dumps(hotels_list, indent=2)[:1000])
            return web.json_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "kind": "artifact-update",
                    "artifact": {"parts": [{"data": []}]},
                    "taskId": task_id
                }
            })

        # 2) Get offers in bulk (fast path)
        offers_data = await amadeus.get(
            "/v3/shopping/hotel-offers",
            params={
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": checkin,
                "checkOutDate": checkout,
                "adults": guests,
                "currency": "USD",
                "include": "HOTEL_IMAGES"
            }
        )

        # Log full offers response for debugging
        _dlog("offers_data response:", json.dumps(offers_data, indent=2)[:2000])
        _dlog("Offers count:", len(offers_data.get("data", [])))
        if not offers_data.get("data"):
            _dlog("No offers returned. Full offers_data:", json.dumps(offers_data, indent=2)[:2000])

        hotels = await normalize_hotels(offers_data, city_code)

        # 3) If TEST returns only a few offers, try per-hotel lookup for remaining ids
        # This helps when only some hotelIds have offers for the given dates.
        if len(hotels) < MAX_HOTELS and time.monotonic() < (deadline - 5.0):
            existing_ids = {h.get("hotel_id") for h in hotels if h.get("hotel_id")}
            remaining_ids = [hid for hid in hotel_ids if hid not in existing_ids]

            for hid in remaining_ids:
                if len(hotels) >= MAX_HOTELS:
                    break
                if time.monotonic() > (deadline - 5.0):
                    break

                try:
                    single = await amadeus.get(
                        "/v3/shopping/hotel-offers/by-hotel",
                        params={
                            "hotelId": hid,
                            "checkInDate": checkin,
                            "checkOutDate": checkout,
                            "adults": guests,
                            "currency": "USD",
                            "include": "HOTEL_IMAGES",
                        },
                    )

                    # Log per-hotel offer response
                    _dlog(f"Per-hotel offer for {hid}:", json.dumps(single, indent=2)[:1000])

                    more = await normalize_hotels(single, city_code, ctx=ctx)
                    for h in more:
                        if len(hotels) >= MAX_HOTELS:
                            break
                        if h.get("hotel_id") and h.get("hotel_id") in existing_ids:
                            continue
                        hotels.append(h)
                        if h.get("hotel_id"):
                            existing_ids.add(h.get("hotel_id"))
                except Exception as ex:
                    # Log error for individual hotel
                    _dlog(f"Per-hotel offers failed for {hid}: {str(ex)}")
                    continue
        
        # Debug: Print final hotel data with image URLs
        _dlog(f"Final hotels count: {len(hotels)}")
        for h in hotels[:2]:  # Print first 2 hotels
            _dlog(f"Hotel: {h.get('name')}, ImageURL: {h.get('imageUrl')[:100] if h.get('imageUrl') else 'MISSING'}")

    except Exception as e:
        hotels = []
        import traceback
        print("ERROR:", str(e))
        traceback.print_exc()

    # Ensure all hotels have valid imageUrl
    for hotel in hotels:
        if not hotel.get("imageUrl") or not isinstance(hotel.get("imageUrl"), str):
            hotel["imageUrl"] = DEFAULT_HOTEL_IMAGE
        elif not (hotel["imageUrl"].startswith("http://") or hotel["imageUrl"].startswith("https://") or hotel["imageUrl"].startswith("data:")):
            hotel["imageUrl"] = DEFAULT_HOTEL_IMAGE
    
    print(f"Returning {len(hotels)} hotels with valid images")

    return web.json_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "kind": "artifact-update",
            "artifact": {"parts": [{"data": hotels}]},
            "taskId": task_id
        }
    })


app = web.Application()
app.router.add_post("/", handle)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
