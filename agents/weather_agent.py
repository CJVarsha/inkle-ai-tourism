import requests

def get_coordinates(city_name: str) -> tuple:
    """
    Get latitude and longitude for a city using OpenStreetMap Nominatim API.
    Returns (lat, lon) tuple or (None, None) if not found.
    """
    GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "inkle-ai-tourism-app (cjvarsha9204@gmail.com)"
    }
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }

    try:
        resp = requests.get(GEOCODER_URL, params=params, headers=headers, timeout=10)
        print(f"[DEBUG] Geocoder response status: {resp.status_code}, body snippet: {resp.text[:200]}")
        resp.raise_for_status()
        data = resp.json()

        if not data:
            print(f"[ERROR] No geocode data returned for city: {city_name}")
            return None, None

        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])
        print(f"[DEBUG] Geocoded city '{city_name}' to lat={lat}, lon={lon}")
        return lat, lon

    except requests.RequestException as e:
        print(f"[ERROR] Geocoding API request failed for city '{city_name}': {e}")
        return None, None
    except (ValueError, KeyError) as e:
        print(f"[ERROR] Parsing geocoding response failed for city '{city_name}': {e}")
        return None, None

def weather_query(city_name: str) -> dict:
    """
    Query Open-Meteo API for current weather and daily forecast.
    Returns a dict with weather data or error reason.
    """
    lat, lon = get_coordinates(city_name)
    if lat is None or lon is None:
        return {
            "success": False,
            "location": city_name,
            "reason": f"Could not determine location coordinates for '{city_name}'. Try specifying a more precise city name."
        }

    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    }

    try:
        resp = requests.get(WEATHER_URL, params=params, timeout=10)
        print(f"[DEBUG] Weather API response status: {resp.status_code}, body snippet: {resp.text[:200]}")
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        result = {
            "success": True,
            "location": city_name,
            "coordinates": (lat, lon),
            "weather": {
                "current": {
                    "temperature": current.get("temperature"),
                    "windspeed": current.get("windspeed"),
                    "weathercode": current.get("weathercode"),
                },
                "today": {
                    "high_temp": daily.get("temperature_2m_max", [None])[0],
                    "low_temp": daily.get("temperature_2m_min", [None])[0],
                    "precipitation": daily.get("precipitation_sum", [None])[0],
                },
            },
        }
        print(f"[DEBUG] Weather data fetched for '{city_name}': {result}")
        return result

    except requests.RequestException as e:
        print(f"[ERROR] Weather API request failed for '{city_name}': {e}")
        return {
            "success": False,
            "location": city_name,
            "reason": "Failed to fetch weather data due to API error."
        }
    except (ValueError, KeyError) as e:
        print(f"[ERROR] Parsing weather API response failed for '{city_name}': {e}")
        return {
            "success": False,
            "location": city_name,
            "reason": "Unexpected data format from weather API."
        }

# For quick local testing
if __name__ == "__main__":
    city = input("Enter a city name to get weather: ")
    result = weather_query(city)
    print(result)
