import requests
from constants import TARGET_TYPES

def fetch_adsbfi():

    planes = {}

    r = requests.get("https://opendata.adsb.fi/api/v2/mil", timeout=10)

    for ac in r.json().get("ac", []):

        if ac.get("t") not in TARGET_TYPES:
            continue

        hex_code = ac.get("hex")

        planes[hex_code] = {
            "alt": ac.get("alt_baro"),
            "hdg": ac.get("track"),
            "lat": ac.get("lat"),
            "lon": ac.get("lon"),
            "type": ac.get("t"),
            "flight": ac.get("flight"),
            "gs": ac.get("gs"),
            "source": "adsb.fi"
        }

    return planes