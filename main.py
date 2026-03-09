import time
import math
import os
import requests
from dotenv import load_dotenv
from opensky_api import OpenSkyApi

load_dotenv()
OPENSKY_USER = os.getenv("OPENSKY_USER")
OPENSKY_PASS = os.getenv("OPENSKY_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TRAINING_MODE = os.getenv("TRAINING_MODE", "False").lower() == "true"

api_opensky = OpenSkyApi(OPENSKY_USER, OPENSKY_PASS)

TARGET_TYPES = ["E6", "R135", "V25", "C32", "E3TF", "B2", "E4", "RQ4", "U2", "B52", "B1", "K35R"]

KNOWN_ICAO_HEX = [

    #E-6B Mercury
    "ae040d", "ae040e", "ae040f", "ae0410", "ae0411", "ae0412",
    "ae0413", "ae0414", "ae0415", "ae0416", "ae0417", "ae0418",
    "ae0419", "ae041a", "ae041b", "ae041c",

    #E-4B Nightwatch
    "adfeb7", "adfeb8", "adfeb9", "adfeba",

    #VC-25A
    "adfdf8", "adfdf9",

    #C-32A
    "ae01e6", "ae01e7", "ae0201", "ae0202",

    #RC-135 Rivet Joint
    "ae01c5", "ae01c6", "ae01c7", "ae01c8", "ae01cb", "ae01cd", "ae01ce",
    "ae01d1", "ae01d2", "ae01d3", "ae01d4", "ae01d5",

    #E-3 Sentry
    "ae11e3", "ae11e4", "ae11e5", "ae11e6", "ae11e7", "ae11e8",

    #RQ-4 Global Hawk
    "ae5414", "ae54b6", "ae7813",

    #U2 Dragon Lady
    "ae094d", "ae0950", "ae0955",

    #B-52 Stratofortress
    "ae586c", "ae586d", "ae586e", "ae5871", "ae5872", "ae5873", "ae5874",
    "ae5881", "ae5889", "ae588a", "ae5893", "ae5897", "ae58a2", "ae58a3",

    #B-1B Lancer
    "ae04a9", "ae04aa", "ae04ab", "ae04ac"

]

flight_history = {}

def check_flight_profile(icao_hex, current_alt, current_hdg, flight_type):
    current_time = time.time()

    if TRAINING_MODE:
        if current_alt == "ground" or current_alt < 10000:
            return False

        if icao_hex not in flight_history:
            flight_history[icao_hex] = {"alt": current_alt, "hdg": current_hdg, "time": current_time}
            return True

        flight_history[icao_hex]["time"] = current_time
        return False

    else:
        if current_alt == "ground" or current_alt < 28000:
            return False

        if not (45 <= current_hdg <= 160):
            return False

        if icao_hex in flight_history:
            prev = flight_history[icao_hex]

            hdg_diff = abs(current_hdg - prev["hdg"])
            time_diff = current_time - prev["time"]

            flight_history[icao_hex] = {"alt": current_alt, "hdg": current_hdg, "time": current_time}

            if hdg_diff < 10 and time_diff < 240:
                return True

        else:
            flight_history[icao_hex] = {"alt": current_alt, "hdg": current_hdg, "time": current_time}

        return False

def fetch_adsbfi():
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

                    if hex_code and alt and hdg:
                        active_planes[hex_code] = {
                            "alt": alt,
                            "hdg": hdg,
                            "lat": lat,
                            "lon": lon,
                            "type": ac_type,
                            "source": "adsb.fi"
                        }
    except Exception as e:
        print(f"Error fetching adsb.fi data: {e}")
    return active_planes

def fetch_opensky():
    active_planes = {}
    try:
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

def send_discord_alert(message):
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message})
        except Exception as e:
            print(f"Error sending Discord alert: {e}")

def estimate_route(lon, hdg):
    if lon is None or hdg is None:
        return "Route: Position unknown"
    if lon < -10:
        return "Route: Transatlantic (West -> East)"

    elif lon > 5 and 100 <= hdg <= 160:
        return "Route: Middle East Deployment (Europe -> Middle East)"

    return "Route: Strategic Movement"

def main():
    print("Startet Tracker. Polling every 60 seconds")
    print("Sende Test-Alert an Discord...")
    test_msg = "🚨 **TEST-ALERT** 🚨\nType: `B52` (Hex: `ae586c`)\nAltitude: `32000 ft` | Heading: `095°`\nSource: *SYSTEM-TEST*"
    send_discord_alert(test_msg)

    while True:
        current_data = {}
        current_data.update(fetch_adsbfi())
        current_data.update(fetch_opensky())

        for hex_code, plane_data in current_data.items():

            is_deploying = check_flight_profile(
                icao_hex = hex_code,
                current_alt = plane_data["alt"],
                current_hdg = plane_data["hdg"],
                flight_type = plane_data["type"]
            )

            if is_deploying:
                map_link = f"https://globe.adsb.fi/?icao={hex_code}"
                route_info = estimate_route(plane_data["lon"], plane_data["hdg"])

                msg = (
                    f"🚨 **ALERT** 🚨 \n"
                    f"Type: `{plane_data['type']}` (Hex: `{hex_code}`) \n"
                    f"{route_info}\n"
                    f"Altitude: `{int(plane_data['alt'])} ft` \n"
                    f"Heading: `{int(plane_data['hdg'])}°` \n"
                    f"Source: *{plane_data['source']}* \n"
                    f"🌍 **Live Map:** {map_link}"
                )
                print(msg)
                send_discord_alert(msg)

        time.sleep(60)

if __name__ == "__main__":
    main()