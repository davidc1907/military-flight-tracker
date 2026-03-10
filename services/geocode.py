import requests
from functools import lru_cache
from config import CFG

@lru_cache(maxsize=512)
def geocode(lat, lon):

    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={lat},{lon}&result_type=country&key={CFG.google_geo_api}"
    )

    r = requests.get(url, timeout=5).json()

    if r["status"] == "ZERO_RESULTS":
        return "Oceanic Airspace"

    if r["status"] == "OK":
        return r["results"][0]["formatted_address"]

    return "Unknown Region"