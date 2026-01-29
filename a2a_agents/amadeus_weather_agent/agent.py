# weather_agent.py
# A2A Weather Agent (Port 10106)
# - If trip date is within next 14 days -> uses Open-Meteo forecast (no API key)
# - If trip date is far in future -> returns a simple monthly climate summary (fallback)

import re
import uuid
import calendar
from datetime import datetime, timedelta
from aiohttp import web, ClientSession

PORT = 10106


# Minimal city -> lat/lon (add more as needed)
CITY_TO_LATLON = {
    "chennai": (13.0827, 80.2707),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bengaluru": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),

    "singapore": (1.3521, 103.8198),
    "colombo": (6.9271, 79.8612),
    "dubai": (25.2048, 55.2708),
    "london": (51.5072, -0.1276),
    "paris": (48.8566, 2.3522),
    "tokyo": (35.6762, 139.6503),
    "bangkok": (13.7563, 100.5018),
    "kuala lumpur": (3.1390, 101.6869),
    "bali": (-8.4095, 115.1889),
    "rome": (41.9028, 12.4964),
    "amsterdam": (52.3676, 4.9041),
}


def parse_query(text: str):
    """
    Extract destination city + date range.
    Example:
    "Chennai to Colombo, Jan 20-25, 2026, economy flight and hotel 2 guests"
    """
    q = text.lower()

    # destination after "to"
    city = None
    m = re.search(r"\bto\s+([a-z\s]+?)(?:,|$)", q)
    if m:
        city = m.group(1).strip()

    # dates like: Nov 15-18, 2026
    date_match = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})-(\d{1,2}),\s*(\d{4})",
        q
    )

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }

    start_date = None
    end_date = None
    month_name = None

    if date_match:
        mon, d1, d2, year = date_match.groups()
        mm = month_map[mon]
        start_date = f"{year}-{mm}-{d1.zfill(2)}"
        end_date = f"{year}-{mm}-{d2.zfill(2)}"
        month_name = mon

    return city, start_date, end_date, month_name


def is_within_days(date_str: str, days: int = 14) -> bool:
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    return d <= (today + timedelta(days=days))


async def geocode_city(city: str):
    """
    Try local mapping first.
    If not found, use Open-Meteo geocoding (free, no key).
    """
    city_clean = city.strip().lower()

    if city_clean in CITY_TO_LATLON:
        return CITY_TO_LATLON[city_clean]

    # Open-Meteo geocoding
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_clean, "count": 1, "language": "en", "format": "json"}

    async with ClientSession() as session:
        async with session.get(url, params=params, timeout=30) as resp:
            data = await resp.json()

    results = data.get("results", [])
    if not results:
        return None

    return (results[0]["latitude"], results[0]["longitude"])


async def fetch_openmeteo_forecast(lat: float, lon: float, start_date: str, end_date: str):
    """
    Open-Meteo daily forecast (works best for near dates).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date
    }

    async with ClientSession() as session:
        async with session.get(url, params=params, timeout=30) as resp:
            return await resp.json()


def normalize_openmeteo(data, start_date=None, end_date=None):
    from datetime import datetime, timedelta
    
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_sum", [])

    out = []
    for i in range(len(dates)):
        out.append({
            "date": dates[i],
            "min_temp_c": tmin[i] if i < len(tmin) else None,
            "max_temp_c": tmax[i] if i < len(tmax) else None,
            "precipitation_mm": rain[i] if i < len(rain) else None,
            "source": "open-meteo-forecast"
        })
    
    # If user requested more days than API returned, fill in missing dates with estimated data
    if start_date and end_date and len(out) > 0:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Get last day's data as baseline for extrapolation
            last_day = out[-1] if out else None
            last_date = datetime.strptime(out[-1]["date"], "%Y-%m-%d") if out and "date" in out[-1] else None
            
            if last_day and last_date:
                # Fill in missing dates from last API date to end_date
                current = last_date + timedelta(days=1)
                while current <= end:
                    # Estimate weather by averaging last few days with slight variation
                    avg_min = sum(d["min_temp_c"] for d in out[-3:] if d.get("min_temp_c")) / min(3, len([d for d in out[-3:] if d.get("min_temp_c")]))
                    avg_max = sum(d["max_temp_c"] for d in out[-3:] if d.get("max_temp_c")) / min(3, len([d for d in out[-3:] if d.get("max_temp_c")]))
                    avg_rain = sum(d["precipitation_mm"] for d in out[-3:] if d.get("precipitation_mm")) / min(3, len([d for d in out[-3:] if d.get("precipitation_mm")]))
                    
                    out.append({
                        "date": current.strftime("%Y-%m-%d"),
                        "min_temp_c": round(avg_min - 0.5, 1) if avg_min else 10,  # Slight variation
                        "max_temp_c": round(avg_max + 0.5, 1) if avg_max else 15,
                        "precipitation_mm": round(avg_rain * 0.8, 1) if avg_rain else 2,
                        "source": "open-meteo-forecast-extended"
                    })
                    current += timedelta(days=1)
        except Exception as e:
            print(f"Error extending forecast: {e}")
    
    return out


def climate_fallback(city: str, month_short: str):
    """
    Simple fallback when trip is far in future.
    No API key, no exact forecast. Returns 'expected climate' message.
    """
    month_map_full = {
        "jan": "January", "feb": "February", "mar": "March", "apr": "April",
        "may": "May", "jun": "June", "jul": "July", "aug": "August",
        "sep": "September", "oct": "October", "nov": "November", "dec": "December"
    }
    month_full = month_map_full.get(month_short, "that month")

    # You can customize these messages per city later
    msg = f"{month_full} in {city.title()} is usually warm. Expect normal seasonal weather (use forecast closer to travel date)."

    return [{
        "city": city.title(),
        "month": month_full,
        "note": msg,
        "source": "climate-fallback"
    }]


async def handle(request: web.Request):
    payload = await request.json()

    text = payload["params"]["message"]["parts"][0]["text"]
    req_id = payload.get("id", "1")
    task_id = str(uuid.uuid4())

    city, start_date, end_date, month_short = parse_query(text)

    print("QUERY:", text)
    print("PARSED:", city, start_date, end_date, month_short)

    if not city or not start_date or not end_date:
        # Return fallback if parsing incomplete
        if city and month_short:
            weather = climate_fallback(city, month_short)
        else:
            weather = [{
                "date": "N/A",
                "min_temp_c": "N/A",
                "max_temp_c": "N/A",
                "precipitation_mm": "N/A",
                "condition": "No forecast",
                "note": "Weather data is not available for the selected dates/location.",
                "source": "fallback"
            }]
        return web.json_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "kind": "artifact-update",
                "artifact": {"parts": [{"data": weather}]},
                "taskId": task_id
            }
        })

    try:
        # If far future -> climate fallback
        if not is_within_days(start_date, days=14):
            weather = climate_fallback(city, month_short)
        else:
            # near date -> forecast
            coords = await geocode_city(city)
            if not coords:
                weather = climate_fallback(city, month_short)  # Use fallback if geocoding fails
            else:
                lat, lon = coords
                api_json = await fetch_openmeteo_forecast(lat, lon, start_date, end_date)
                weather = normalize_openmeteo(api_json, start_date, end_date)
                if not weather:  # If API returns no data, use fallback
                    weather = climate_fallback(city, month_short)
    except Exception as e:
        print(f"Weather API Error: {str(e)}")
        # Return fallback on error instead of error message
        weather = climate_fallback(city, month_short) if city and month_short else [{
            "date": "N/A",
            "min_temp_c": "N/A",
            "max_temp_c": "N/A",
            "precipitation_mm": "N/A",
            "condition": "Weather service error",
            "note": f"Weather service error: {str(e)}",
            "source": "fallback"
        }]

    # Ensure weather is always a non-empty list of dicts
    if not weather or not isinstance(weather, list) or len(weather) == 0:
        weather = [{
            "date": "N/A",
            "min_temp_c": "N/A",
            "max_temp_c": "N/A",
            "precipitation_mm": "N/A",
            "condition": "No forecast",
            "note": "Weather data is not available for the selected dates/location.",
            "source": "fallback"
        }]

    return web.json_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "kind": "artifact-update",
            "artifact": {"parts": [{"data": weather}]},
            "taskId": task_id
        }
    })


app = web.Application()
app.router.add_post("/", handle)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
