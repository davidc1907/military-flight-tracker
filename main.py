import time
import math
import os
import requests
from dotenv import load_dotenv
from opensky_api import OpenSkyApi

# Load runtime settings from .env
load_dotenv()
OPENSKY_USER = os.getenv("OPENSKY_USER")
OPENSKY_PASS = os.getenv("OPENSKY_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TRAINING_MODE = os.getenv("TRAINING_MODE", "False").lower() == "true"
GOOGLE_GEO_API = os.getenv("GOOGLE_GEO_API")
# Minimum wait time between alerts for the same aircraft (seconds)
ALERT_COOLDOWN = 7200

api_opensky = OpenSkyApi(OPENSKY_USER, OPENSKY_PASS)

# Military aircraft model/type codes to track from ADS-B Exchange feed
TARGET_TYPES = ["E6", "R135", "V25", "C32", "E3TF", "B2", "E4", "RQ4", "U2", "B52", "B1", "K35R", "MQ9", "P8", "MQ4", "F35", "F22", "EUFI", "V22"]

# Known ICAO24 addresses for high-interest aircraft tracked from OpenSky
KNOWN_ICAO_HEX = [

    # E-6B Mercury
    "ae040d", "ae040e", "ae040f", "ae0410", "ae0411", "ae0412",
    "ae0413", "ae0414", "ae0415", "ae0416", "ae0417", "ae0418",
    "ae0419", "ae041a", "ae041b", "ae041c",

    # E-4B Nightwatch
    "adfeb7", "adfeb8", "adfeb9", "adfeba",

    # VC-25A
    "adfdf8", "adfdf9", "adfeb2", "adfeb3",

    # C-32A
    "ae01e6", "ae01e7", "ae0201", "ae0202", "ae4ae8", "ae4ae9", "ae4aea", "ae4aeb",

    # RC-135 Rivet Joint
    "ae01c5", "ae01c6", "ae01c7", "ae01c8", "ae01cb", "ae01cd", "ae01ce",
    "ae01d1", "ae01d2", "ae01d3", "ae01d4", "ae01d5",

    # E-3 Sentry
    "ae11e3", "ae11e4", "ae11e5", "ae11e6", "ae11e7", "ae11e8",

    # RQ-4 Global Hawk
    "ae5414", "ae54b6", "ae7813",

    # U-2 Dragon Lady
    "ae094d", "ae0950", "ae0955",

    # B-52 Stratofortress
    "ae586c", "ae586d", "ae586e", "ae5871", "ae5872", "ae5873", "ae5874",
    "ae5881", "ae5889", "ae588a", "ae5893", "ae5897", "ae58a2", "ae58a3",

    # B-1B Lancer
    "ae04a9", "ae04aa", "ae04ab", "ae04ac"

]

# VIP aircraft that should trigger high-priority alerts
SPECIAL_TARGETS = {
    "adfdf8": "🇺🇸 AIR FORCE ONE",
    "adfdf9": "🇺🇸 AIR FORCE ONE",
    "adfeb2": "🇺🇸 AIR FORCE ONE",
    "adfeb3": "🇺🇸 AIR FORCE ONE",
    "ae01e6": "🇺🇸 AIR FORCE TWO",
    "ae01e7": "🇺🇸 AIR FORCE TWO",
    "ae0201": "🇺🇸 AIR FORCE TWO",
    "ae0202": "🇺🇸 AIR FORCE TWO",
    "ae4ae8": "🇺🇸 AIR FORCE TWO",
    "ae4ae9": "🇺🇸 AIR FORCE TWO",
    "ae4aea": "🇺🇸 AIR FORCE TWO",
    "ae4aeb": "🇺🇸 AIR FORCE TWO"
}

# Per-aircraft cache used for movement analysis and cooldown tracking
flight_history = {}

def check_flight_profile(icao_hex, current_alt, current_hdg, flight_type):
    """Decide whether a flight profile is alert-worthy based on altitude, heading, and stability."""
    current_time = time.time()

    # First observation: initialize tracking state.
    if icao_hex not in flight_history:
        flight_history[icao_hex] = {
            "alt": current_alt,
            "hdg": current_hdg,
            "time": current_time,
            "last_alert": 0
        }
        return True if TRAINING_MODE else False

    prev = flight_history[icao_hex]
    time_since_alert = current_time - prev.get("last_alert", 0)

    if TRAINING_MODE:
        # In training mode, alert on high-altitude sightings only, with cooldown.
        if current_alt == "ground" or current_alt < 10000:
            return False
        if time_since_alert > ALERT_COOLDOWN:
            flight_history[icao_hex]["last_alert"] = current_time
            return True
        return False

    else:
        # In normal mode, apply stricter filters for potential deployment behavior.
        if current_alt == "ground" or current_alt < 28000:
            return False
        if not (45 <= current_hdg <= 160):
            return False

        hdg_diff = abs(current_hdg - prev["hdg"])
        time_since_last_scan = current_time - prev["time"]

        # Keep latest telemetry for the next decision cycle.
        flight_history[icao_hex].update({"alt": current_alt, "hdg": current_hdg, "time": current_time})

        # Stable heading over a short period can indicate sustained route commitment.
        if hdg_diff < 10 and time_since_last_scan < 240:
            if time_since_alert > ALERT_COOLDOWN:
                flight_history[icao_hex]["last_alert"] = current_time
                return True
        return False

def fetch_adsbfi():
    """Fetch active military flights from ADS-B API and return normalized aircraft data."""
    active_planes = {}
    try:
        response = requests.get("https://opendata.adsb.fi/api/v2/mil", timeout=10)
        if response.status_code == 200:
            data = response.json()
            for plane in data.get("ac", []):
                ac_type = plane.get("t")
                if ac_type in TARGET_TYPES:
                    hex_code = plane.get("hex")
                    alt = plane.get("alt_baro")
                    hdg = plane.get("track")
                    lat = plane.get("lat")
                    lon = plane.get("lon")

                    # Require basic position and movement fields before using a record.
                    if hex_code and alt and hdg:
                        active_planes[hex_code] = {
                            "alt": alt,
                            "hdg": hdg,
                            "lat": lat,
                            "lon": lon,
                            "type": ac_type,
                            "flight": plane.get("flight", "N/A"),
                            "desc": plane.get("desc", ac_type),
                            "gs": plane.get("gs", 0),
                            "source": "adsb.fi"
                        }
    except Exception as e:
        print(f"Error fetching adsb.fi data: {e}")
    return active_planes

def fetch_opensky():
    """Fetch known target aircraft from OpenSky within a North Atlantic bounding box."""
    active_planes = {}
    try:
        # (min_lat, max_lat, min_lon, max_lon)
        bbox_atlantic = (30.0, 60.0, -70.0, 40.0)
        states = api_opensky.get_states(bbox = bbox_atlantic)

        if states and states.states:
            for s in states.states:
                if s.icao24 in KNOWN_ICAO_HEX:
                    alt_feet = s.baro_altitude * 3.28084 if s.baro_altitude else 0
                    hdg = s.true_track

                    if alt_feet and hdg:
                        active_planes[s.icao24] = {
                            "alt": alt_feet,
                            "hdg": hdg,
                            "lat": s.latitude,
                            "lon": s.longitude,
                            "type": s.callsign,
                            "source": "opensky"
                        }
    except Exception as e:
        print(f"Error fetching opensky data: {e}")
    return active_planes

def get_google_location(lat, lon):
    if lat is None or lon is None:
        return "Position unknown"

    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&result_type=country&key={GOOGLE_GEO_API}"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            if data.get("status") == "ZERO_RESULTS":
                return "Offshore / Oceanic Airspace"

            elif data.get("status") == "OK" and len(data.get("results")) > 0:
                address = data["results"][0].get("formatted_address", "Unknown Region")
                return f"🗺️ {address}"

            else:
                return "Unknown Region"
    except Exception as e:
        print(f"Error fetching Google location: {e}")

    return "Offline"


def send_discord_alert(message):
    """Post a plain-text alert message to the configured Discord webhook."""
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message})
        except Exception as e:
            print(f"Error sending Discord alert: {e}")

def estimate_route(lon, hdg):
    """Roughly classify route intent from longitude and heading."""
    if lon is None or hdg is None:
        return "Route: Position unknown"
    if lon < -10:
        return "Route: Transatlantic (West -> East)"

    elif lon > 5 and 100 <= hdg <= 160:
        return "Route: Middle East Deployment (Europe -> Middle East)"

    return "Route: Strategic Movement"

def main():
    """Continuously poll flight sources, detect events, and send Discord alerts."""
    print("Startet Tracker. Polling every 60 seconds")
    print("Sende Test-Alert an Discord...")
    # Send one startup test message to confirm webhook delivery.
    test_msg = "🚨 **TEST-ALERT** 🚨\nType: `B52` (Hex: `ae586c`)\nAltitude: `32000 ft` | Heading: `095°`\nSource: *SYSTEM-TEST*"
    send_discord_alert(test_msg)

    while True:
        current_data = {}
        # Merge both feeds (later sources overwrite duplicate ICAO keys).
        current_data.update(fetch_adsbfi())
        current_data.update(fetch_opensky())

        for hex_code, plane_data in current_data.items():
            is_deploying = check_flight_profile(
                icao_hex=hex_code,
                current_alt=plane_data["alt"],
                current_hdg=plane_data["hdg"],
                flight_type=plane_data["type"]
            )

            is_special = hex_code in SPECIAL_TARGETS
            current_time = time.time()

            last_vip_alert = flight_history.get(hex_code, {}).get("last_alert", 0)
            vip_cooldown_ok = (current_time - last_vip_alert) > ALERT_COOLDOWN

            if is_deploying or (is_special and vip_cooldown_ok):
                route_info = estimate_route(plane_data.get("lon"), plane_data.get("hdg"))
                map_link = f"https://globe.adsb.fi/?icao={hex_code}" if plane_data.get("lon") else "No coordinates"
                location_info = get_google_location(plane_data.get("lat"), plane_data.get("lon"))
                callsign = plane_data.get("flight", "").strip()
                if not callsign:
                    callsign = "N/A"

                full_desc = plane_data.get("desc", plane_data.get("t", "Unknown Type"))

                if is_special:
                    if hex_code not in flight_history:
                        flight_history[hex_code] = {}
                    flight_history[hex_code]["last_alert"] = current_time
                    prefix = f"⭐ **PRIORITY ALERT: {SPECIAL_TARGETS[hex_code]}** ⭐"
                else:
                    prefix = "🚨 **STRATEGIC ALERT** 🚨"

                msg = (
                    f"{prefix}\n"
                    f"**Callsign:** `{callsign}`\n"
                    f"**Type:** {full_desc} (Hex: `{hex_code}`)\n"
                    f"**Location:** {location_info}\n"
                    f"**Altitude:** `{int(plane_data['alt'])} ft`\n"
                    f"**Speed:** `{int(plane_data.get('gs', 0))} kts`\n"
                    f"**Heading:** `{int(plane_data['hdg'])}°`\n"
                    f"**Source:** *{plane_data['source']}*\n"
                    f"🌍 **Live Map:** {map_link}"
                )
                print(msg)
                send_discord_alert(msg)

        # Poll interval
        time.sleep(60)

if __name__ == "__main__":
    main()