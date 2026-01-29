# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import asyncio
import requests
import uuid
from datetime import datetime
from typing import Dict, Any

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Agent ports configuration
AGENTS = {
    "flight": 10103,
    "hotel": 10104,
    "weather": 10106,
}


# Basic airline metadata used to enhance flight display.
# Static files are served from the local "images" directory under the
# "/static" path (see __main__.py). So all logo URLs should start with
# "/static/..." and the actual image files should live under
# Airline metadata used to enhance flight display.
# We keep only names here and fetch logo URLs dynamically via SerpAPI.
DEFAULT_AIRLINE_LOGO_URL = "https://www.aircanada.com/content/dam/aircanada/portal/images/tiles/fly/onboard/tile50-our-fleet.jpg"

AIRLINE_INFO: Dict[str, Dict[str, str]] = {
    "AA": {"name": "American Airlines"},
    "DL": {"name": "Delta Air Lines"},
    "UA": {"name": "United Airlines"},
    "BA": {"name": "British Airways"},
    "AF": {"name": "Air France"},
    "LH": {"name": "Lufthansa"},
    "EK": {"name": "Emirates"},
    "QR": {"name": "Qatar Airways"},
    "SQ": {"name": "Singapore Airlines"},
    "TK": {"name": "Turkish Airlines"},
}

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
_AIRLINE_LOGO_CACHE: Dict[str, str] = {}


def get_airline_logo_url(airline: str, airline_name: str) -> str:
    """Return a logo URL for the airline, using SerpAPI when possible.

    Results are cached per airline code to avoid repeated SerpAPI calls.
    """

    code = (airline or "").upper()
    # Hardcoded image for Virgin Atlantic
    if code in ("VS",) or (airline_name or "").lower().startswith("virgin atlantic"):
        return "https://images.ctfassets.net/rxqefefl3t5b/3cNPacvs5XOn36kvDhDkXf/a9a46bd03c2e5b9da9c5398ae14eb34b/A350_Air2Air2019_Retouched_DSC4963_EM4.jpg?fl=progressive&q=80"

    if code in _AIRLINE_LOGO_CACHE:
        return _AIRLINE_LOGO_CACHE[code]

    if not SERPAPI_KEY:
        return DEFAULT_AIRLINE_LOGO_URL

    try:
        params = {
            "engine": "google_images",
            "q": f"{airline_name} logo",
            "api_key": SERPAPI_KEY,
            "safe": "active",
            "num": 5,
        }
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=5)
        data = resp.json()
        images = data.get("images_results") or []
        for img in images:
            url = img.get("original") or img.get("thumbnail") or ""
            if isinstance(url, str) and url.startswith("http"):
                _AIRLINE_LOGO_CACHE[code] = url
                return url
    except Exception as e:
        logger.warning(f"SerpAPI airline logo lookup failed for {airline}: {e}")

    return DEFAULT_AIRLINE_LOGO_URL


def call_agent_sync(port: int, query: str) -> Dict[str, Any]:
    """Call an agent via HTTP synchronously."""
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": query}]
            }
        }
    }

    try:
        response = requests.post(f"http://localhost:{port}", json=payload, timeout=60.0)
        result = response.json()
        logger.info(f"Agent on port {port} responded successfully")
        return result
    except Exception as e:
        logger.error(f"Error calling agent on port {port}: {str(e)}")
        return {"error": str(e), "port": port}


def extract_data(resp: Dict[str, Any]) -> Any:
    """Extract data from agent response."""
    try:
        return resp.get("result", {}).get("artifact", {}).get("parts", [{}])[0].get("data", [])
    except Exception as e:
        logger.error(f"Error extracting data from response: {str(e)}")
        return []


def get_restaurants(cuisine: str, location: str,  tool_context: ToolContext, count: int = 5) -> str:
    """Call this tool to get a list of restaurants based on a cuisine and location.
    'count' is the number of restaurants to return.
    """
    logger.info(f"--- TOOL CALLED: get_restaurants (count: {count}) ---")
    logger.info(f"  - Cuisine: {cuisine}")
    logger.info(f"  - Location: {location}")

    items = []
    if "new york" in location.lower() or "ny" in location.lower():
        try:
            script_dir = os.path.dirname(__file__)
            file_path = os.path.join(script_dir, "restaurant_data.json")
            with open(file_path) as f:
                restaurant_data_str = f.read()
                if base_url := tool_context.state.get("base_url"):                    
                    restaurant_data_str = restaurant_data_str.replace("http://localhost:10002", base_url)
                    logger.info(f'Updated base URL from tool context: {base_url}')
                all_items = json.loads(restaurant_data_str)        

            # Slice the list to return only the requested number of items
            items = all_items[:count]
            logger.info(
                f"  - Success: Found {len(all_items)} restaurants, returning {len(items)}."
            )

        except FileNotFoundError:
            logger.error(f"  - Error: restaurant_data.json not found at {file_path}")
        except json.JSONDecodeError:
            logger.error(f"  - Error: Failed to decode JSON from {file_path}")

    return json.dumps(items)


def get_weather_emoji(condition: str) -> str:
    """Map weather condition to emoji."""
    if not condition:
        return "🌤️"
    
    condition = condition.lower()
    if "rain" in condition:
        return "🌧️"
    elif "cloud" in condition:
        return "☁️"
    elif "clear" in condition or "sunny" in condition:
        return "☀️"
    elif "snow" in condition:
        return "❄️"
    elif "wind" in condition:
        return "💨"
    elif "fog" in condition or "mist" in condition:
        return "🌫️"
    elif "thunder" in condition or "storm" in condition:
        return "⛈️"
    else:
        return "🌤️"


def format_weather_data(weather_raw: Any) -> list:
    """Transform weather data into separate daily weather cards in vertical direction only.
    Each day gets its own card with condition, temp, and precipitation.
    """
    if not weather_raw:
        return []
    
    # Handle both list and single object
    weather_list = weather_raw if isinstance(weather_raw, list) else [weather_raw]
    formatted = []
    
    for weather_item in weather_list:
        if isinstance(weather_item, dict):
            # Determine if this is real forecast or fallback climate data
            is_fallback = weather_item.get("source") == "climate-fallback"
            
            if is_fallback:
                # Fallback format: {city, month, note, source}
                # Show as a single card for fallback
                formatted.append({
                    "date": weather_item.get("city", "Unknown"),
                    "temperature": weather_item.get("month", "N/A"),
                    "condition": "Seasonal",
                    "emoji": "🌍",
                    "precipitation": weather_item.get("note", "No forecast available")
                })
            else:
                # Real forecast format: {date, min_temp_c, max_temp_c, precipitation_mm, condition, source}
                # Create a separate card for each day
                condition = weather_item.get("condition", "Clear")
                emoji = get_weather_emoji(condition)
                
                precip = weather_item.get('precipitation_mm', '0')
                try:
                    precip_val = float(precip)
                except (TypeError, ValueError):
                    precip_val = 0
                if precip_val > 1.5:
                    precip_str = f"🌦️ {precip}mm"
                elif precip_val > 0:
                    precip_str = f"💧 {precip}mm"
                else:
                    precip_str =" "
                formatted.append({
                    "date": weather_item.get("date", "Unknown"),
                    "temperature": f"{weather_item.get('min_temp_c', 'N/A')}°C - {weather_item.get('max_temp_c', 'N/A')}°C",
                    "condition": condition,
                    "emoji": emoji,
                    "precipitation": precip_str
                })
    
    return formatted


def format_hotel_data(hotels_raw: Any) -> list:
    """Transform hotel data to match UI template format. Returns empty list if no hotels."""
    if not hotels_raw:
        logger.warning("No hotel data received from hotel agent")
        return []
    
    # Handle both list and single object
    hotel_list = hotels_raw if isinstance(hotels_raw, list) else [hotels_raw]
    formatted = []
    
    for hotel_item in hotel_list:
        if isinstance(hotel_item, dict):
            name = hotel_item.get("name") or hotel_item.get("hotel_name") or "Unknown Hotel"
            rate_total = hotel_item.get("rate_total")
            currency = hotel_item.get("currency") or "USD"
            price = hotel_item.get("price") or (f"{rate_total} {currency}" if rate_total else f"N/A {currency}")
                # Hardcoded image for London Marriott Hotel County Hall
            if name.strip().lower() == "london marriott hotel county hall":
                image_url = "https://cache.marriott.com/content/dam/marriott-digital/mc/emea/hws/l/lonch/en_us/photo/unlimited/assets/lonch-exterior-1425.jpg"
            elif name.strip().lower() == "w london":
                image_url= "https://www.momondo.in/rimg/himg/5a/bc/81/leonardo-329298-977713-911208.jpg?width=968&height=607&crop=true"
            else:
                image_url = "https://www.ahstatic.com/photos/1785_ho_00_p_1024x768.jpg"
                #hotel_item.get("imageUrl") or hotel_item.get("el_image_urhotl") or

            formatted.append({
                "name": name,
                "hotel_id": hotel_item.get("hotel_id", "N/A"),
                "check_in": hotel_item.get("check_in", "N/A"),
                "check_out": hotel_item.get("check_out", "N/A"),
                "price": price,
                "currency": currency,
                "rate_total": rate_total or "N/A",
                "room_type": hotel_item.get("room_type", "N/A"),
                "rating": hotel_item.get("rating", "★★★★☆"),
                "imageUrl": image_url
            })
    
    return formatted if formatted else format_hotel_data(None)  # Use fallback if no valid hotels


def format_flight_data(flights_raw: Any, base_url: str | None = None) -> list:
    """Transform flight data into display-friendly strings for the Flights tab.

    base_url is the public URL of this agent (e.g., http://localhost:10002).
    It is used to build logo URLs like {base_url}/images/airlines/AA.png.
    """
    if not flights_raw:
        return []

    flights_list = flights_raw if isinstance(flights_raw, list) else [flights_raw]
    formatted: list[dict[str, str]] = []

    for flight in flights_list:
        if not isinstance(flight, dict):
            continue

        airline = flight.get("airline", "Unknown")
        dep = flight.get("departure")
        arr = flight.get("arrival")
        stops = flight.get("stops", 0) or 0
        total_price = flight.get("total_price") or flight.get("price")
        currency = flight.get("currency") or "USD"

        # Look up airline metadata (full name) and dynamic logo URL via SerpAPI
        meta = AIRLINE_INFO.get(airline, {})
        airline_name = meta.get("name", airline)
        logo_url = get_airline_logo_url(airline, airline_name)

        # Format times as HH:MM (local) when possible
        def _fmt_time(value: str | None) -> str:
            if not value or not isinstance(value, str):
                return "--:--"
            try:
                # Amadeus returns ISO without timezone (local time)
                dt = datetime.fromisoformat(value)
                return dt.strftime("%H:%M")
            except Exception:
                return value

        dep_time = _fmt_time(dep)
        arr_time = _fmt_time(arr)

        # Compute simple duration if both times parse cleanly
        duration_text = ""
        try:
            dt_dep = datetime.fromisoformat(dep) if isinstance(dep, str) else None
            dt_arr = datetime.fromisoformat(arr) if isinstance(arr, str) else None
            if dt_dep and dt_arr and dt_arr > dt_dep:
                mins = int((dt_arr - dt_dep).total_seconds() // 60)
                hours, minutes = divmod(mins, 60)
                if hours and minutes:
                    duration_text = f"{hours} hrs {minutes} min"
                elif hours:
                    duration_text = f"{hours} hrs"
                else:
                    duration_text = f"{minutes} min"
        except Exception:
            duration_text = ""

        if isinstance(stops, (int, float)) and int(stops) == 0:
            stops_label = "Non-stop"
        else:
            try:
                s = int(stops)
            except Exception:
                s = 1
            stops_label = f"{s} stop" if s == 1 else f"{s} stops"

        # Build human-friendly display strings for individual labeled lines
        price = f"{total_price} {currency}" if total_price else f"N/A {currency}"

        airline_line = f"Airline: {airline_name} ({airline})"
        dep_arr_line = f"Departure  Arrival: {dep_time}  {arr_time}"
        duration_line = f"Duration: {duration_text or 'N/A'}"
        stops_line = f"Stops: {stops_label}"
        price_line = f"Price: {price}"

        # Also keep a compact info string for any older templates that still use it
        info_parts = [airline, f"{dep_time}  {arr_time}"]
        if duration_text:
            info_parts.append(duration_text)
        info_parts.append(stops_label)
        info = ", ".join(info_parts)

        formatted.append({
            "info": info,
            "price": price,
            "airline": airline,
            "airlineName": airline_name,
            "logoUrl": logo_url,
            "airlineLine": airline_line,
            "depArrLine": dep_arr_line,
            "durationLine": duration_line,
            "stopsLine": stops_line,
            "priceLine": price_line,
        })

    return formatted

def group_into_rows(items, row_size=3):
    """Group a flat list into sublists of length row_size."""
    return [items[i:i+row_size] for i in range(0, len(items), row_size)]

def get_complete_trip(query: str, tool_context: ToolContext) -> str:
    """Call this tool to get a complete trip with flights, hotels, weather, and restaurants.
    Use this when the user asks for a complete trip or multiple services.
    """
    logger.info(f"--- TOOL CALLED: get_complete_trip ---")
    logger.info(f"  - Query: {query}")

    base_url = None
    try:
        base_url = tool_context.state.get("base_url")  # set by RestaurantAgent
        if base_url:
            logger.info(f"  - Using base_url for assets: {base_url}")
    except Exception:
        base_url = None
    
    try:
        # Call all agents synchronously
        flight_resp = call_agent_sync(AGENTS["flight"], query)
        hotel_resp = call_agent_sync(AGENTS["hotel"], query)
        weather_resp = call_agent_sync(AGENTS["weather"], query)
        
        # Extract and format data from responses
        flights_raw = extract_data(flight_resp)
        weather_raw = extract_data(weather_resp)
        hotels_raw = extract_data(hotel_resp)
        
        # Format weather data
        weather_formatted = format_weather_data(weather_raw)

        # Group weather cards into rows of 3 for grid display, and wrap each row and card as valueMaps with keys
        weather_rows = []
        grouped = group_into_rows(weather_formatted, row_size=3)
        for row_idx, row in enumerate(grouped, 1):
            weather_rows.append({
                "key": f"row{row_idx}",
                "valueMap": [
                    {
                        "key": f"card{card_idx+1}",
                        "valueMap": [
                            {"key": k, "valueString": v} for k, v in card.items()
                        ]
                    }
                    for card_idx, card in enumerate(row)
                ]
            })
        logger.debug(f"weatherRows structure: {json.dumps(weather_rows, indent=2)}")
        
        # Format hotels to valueMap for A2UI binding
        hotels_formatted = format_hotel_data(hotels_raw)
        hotels_valuemap = []
        for idx, hotel_item in enumerate(hotels_formatted, 1):
            hotels_valuemap.append({
                "key": f"hotel{idx}",
                "valueMap": [
                    {"key": "name", "valueString": hotel_item.get("name", "N/A")},
                    {"key": "check_in", "valueString": hotel_item.get("check_in", "N/A")},
                    {"key": "check_out", "valueString": hotel_item.get("check_out", "N/A")},
                    {"key": "price", "valueString": hotel_item.get("price", "N/A")},
                    {"key": "rating", "valueString": hotel_item.get("rating", "N/A")},
                    {"key": "imageUrl", "valueString": hotel_item.get("imageUrl", "https://www.ahstatic.com/photos/1785_ho_00_p_1024x768.jpg")}
                ]
            })

        # Format flights into friendly info/price strings used by the Flights tab,
        # including airline logo URLs resolved against base_url when available.
        flights_formatted = format_flight_data(flights_raw, base_url=base_url)
        
        trips_data = {
            "flights": flights_formatted,
            "hotels": hotels_valuemap,
            #"weather": weather_valuemap,
            "weatherRows": weather_rows,
        }

        logger.info(f"  - Success: Complete trip data retrieved with {len(weather_rows)} weather rows")
        return json.dumps(trips_data)
    except Exception as e:
        logger.error(f"  - Error: {str(e)}")
        return json.dumps({"error": str(e)})
print("SERPAPI_KEY present in tools.py:", bool(SERPAPI_KEY))

