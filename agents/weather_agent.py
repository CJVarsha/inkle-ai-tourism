import requests

def get_coordinates(city_name: str) -> tuple:
    """
    Use OpenStreetMap Nominatim to get latitude and longitude for a city.
    Returns a tuple (lat, lon) or (None, None) on failure.
    """
    GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
    try:
        params = {
            'q': city_name,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'InkleAI-Tourism-Agent/1.0 (contact: your-email@example.com)'
        }
        resp = requests.get(GEOCODER_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and 'lat' in data[0] and 'lon' in data[0]:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            print(f"[DEBUG] Geocoded city '{city_name}' to lat={lat}, lon={lon}")
            return lat, lon
        else:
            print(f"[WARN] No geocode result for '{city_name}'")
            return None, None
    except Exception as e:
        print(f"[ERROR] Geocoding failed for '{city_name}': {e}")
        return None, None

def weather_query(city_name: str) -> dict:
    """
    Query Open-Meteo API for current weather and daily forecasts for a city.
    Returns a dict with weather data or an error message.
    """
    lat, lon = get_coordinates(city_name)
    if lat is None or lon is None:
        return {
            "success": False,
            "location": city_name,
            "reason": f"Could not resolve location '{city_name}'. Try a major city like 'Paris, France'."
        }

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    }
    try:
        print(f"[DEBUG] Querying Open-Meteo for '{city_name}' at lat={lat}, lon={lon}")
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        weather_info = {
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
                    "precipitation": daily.get("precipitation_sum", [None])[0]
                }
            },
            "success": True
        }
        print(f"[DEBUG] Received weather data for '{city_name}': {weather_info}")
        return weather_info
    except Exception as e:
        print(f"[ERROR] Open-Meteo API call failed for '{city_name}': {e}")
        return {
            "success": False,
            "location": city_name,
            "reason": "Failed to fetch weather data due to API error."
        }

# Optional quick test code if running script directly
if __name__ == "__main__":
    city = input("Enter city to get weather for: ")
    result = weather_query(city)
    print(result)
