# weather_api.py
import requests
from typing import Tuple

# === Set your API key here ===
API_KEY = "c9ca6b018ef6d2f8fe093cd27b45ef2a"  # Replace with your actual key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"  # HTTPS

# Default city weather (used if API key missing or network fails)
DEFAULT_WEATHER = {
    "Delhi": {"main": "Clear", "visibility_km": 10.0},
    "Mumbai": {"main": "Clouds", "visibility_km": 8.0},
    "Bangalore": {"main": "Rain", "visibility_km": 9.0},
    "Kolkata": {"main": "Fog", "visibility_km": 6.0},
}

def _map_weather_main(main_str: str) -> str:
    s = main_str.lower()
    if "clear" in s:
        return "Clear"
    if "cloud" in s:
        return "Clouds"
    if "rain" in s or "drizzle" in s:
        return "Rain"
    if "mist" in s or "fog" in s or "haze" in s:
        return "Fog"
    return main_str.title()

def get_weather(city: str = "Delhi") -> Tuple[str, float, bool]:
    """
    Returns: (weather_description:str, visibility_km:float, ok:bool)
    ok==True means API returned a valid response; False means default/fallback used.
    """
    city = city.strip().title()

    # Debug prints
    print("Requested city:", city)
    print("Using API key:", API_KEY)

    # If no API key, use default
    if not API_KEY:
        w = DEFAULT_WEATHER.get(city, {"main": "Clear (default)", "visibility_km": 10.0})
        return w["main"], w["visibility_km"], False

    # Try API call
    try:
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        r = requests.get(BASE_URL, params=params, timeout=6.0)
        r.raise_for_status()  # Raises exception for HTTP errors
        data = r.json()

        # Parse response
        main = data["weather"][0]["main"]
        desc = _map_weather_main(main)

        # Correct handling of visibility
        visibility_m = data.get("visibility")
        if visibility_m is None:
            visibility_km = 10.0  # fallback default
        else:
            visibility_km = float(visibility_m) / 1000.0

        return desc, visibility_km, True
    except Exception as e:
        print("Weather API error:", e)
        # fallback if network/API fails
        w = DEFAULT_WEATHER.get(city, {"main": "Clear (default)", "visibility_km": 10.0})
        return w["main"], w["visibility_km"], False

# Optional: test
if __name__ == "__main__":
    print(get_weather("Delhi"))
    print(get_weather("Mumbai"))
    print(get_weather("UnknownCity"))
