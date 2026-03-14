import time
import logging

from utils.logging import setup_logging
from sources.adsbfi import fetch_adsbfi
from sources.opensky import fetch_opensky
from constants import SPECIAL_TARGETS

from core.tracker import check_profile
from core.history import cleanup, flight_history
from core.routing import estimate_route
from services.geocode import geocode
from services.discord import send_strategic_alert
from config import CFG
from sources.flightradar import fetch_flightradar

setup_logging()
logger = logging.getLogger(__name__)


# Process one aircraft and trigger alert if filters pass
def process_target(hex_code, plane):
    try:
        raw_alt = plane.get("alt", 0)
        alt = int(raw_alt) if str(raw_alt).isdigit() else 0
        hdg = int(plane.get("hdg") or plane.get("track") or 0)
    except (ValueError, TypeError):
        return

    profile_score = check_profile(hex_code, alt, hdg, plane.get("lat"), plane.get("lon"), plane)

    if profile_score:
        logger.info(f"DEBUG: {hex_code} passed filter with Score: {profile_score}")
    else:
        pass

    is_special = hex_code in SPECIAL_TARGETS

    current_time = time.time()
    last_vip_alert = flight_history.get(hex_code, {}).get("last_alert", 0)
    vip_cooldown_ok = (current_time - last_vip_alert) > CFG.alert_cooldown_sec

    if profile_score or (is_special and vip_cooldown_ok):

        priority_tag = "STANDARD"

        if is_special:
            priority_tag = "VIP"
        elif profile_score >= 85:
            priority_tag = "HIGH"
        elif profile_score >= 70:
            priority_tag = "MEDIUM"

        location = geocode(plane.get("lat"), plane.get("lon"))

        raw_callsign = str(plane.get("flight") or plane.get("callsign") or "").strip()
        callsign = raw_callsign if raw_callsign else "N/A"
        speed = plane.get("gs") or plane.get("speed") or "N/A"
        desc = plane.get("desc") or plane.get("type") or "Unknown Aircraft"
        reg = plane.get("reg") or "N/A"
        ownOp = plane.get("ownOp") or "Unknown Operator"
        squawk = plane.get("squawk") or "N/A"
        emergency = plane.get("emergency") or "none"
        category = plane.get("category") or "N/A"
        v_speed =plane.get("v_speed") or "N/A"

        if is_special:
            if hex_code not in flight_history:
                flight_history[hex_code] = {"time": current_time}
            flight_history[hex_code]["last_alert"] = current_time

        send_strategic_alert(
            callsign = callsign,
            hex_code = hex_code,
            full_desc = desc,
            location = location,
            alt = alt,
            speed = speed,
            heading = hdg,
            source = plane.get("source", "API"),
            priority_tag = priority_tag,
            reg = reg,
            ownOp = ownOp,
            squawk = squawk,
            v_speed = v_speed,
            emergency = emergency,
            category = category
        )
        logger.info(f"Sent alert for {callsign} ({hex_code})")


def main():
    logger.info("Tracker active. Polling every %d seconds", CFG.poll_interval_sec)

    while True:
        cleanup()

        planes = {}
        adsbfi_planes = fetch_adsbfi()
        opensky_planes = fetch_opensky()
        fr24_planes = fetch_flightradar()

        # Prefer adsb.fi, enrich with OpenSky/FR24 when missing position/altitude
        for hex_code, plane in adsbfi_planes.items():
            planes[hex_code] = plane

        for hex_code, plane in opensky_planes.items():
            if hex_code not in planes:
                planes[hex_code] = plane
            else:
                if planes[hex_code].get("lat") is None and plane.get("lat") is not None:
                    planes[hex_code]["lat"] = plane["lat"]
                    planes[hex_code]["lon"] = plane["lon"]
                    planes[hex_code]["source"] = "adsb.fi + OpenSky"

        for hex_code, plane in fr24_planes.items():
            if hex_code not in planes:
                planes[hex_code] = plane
            else:
                if planes[hex_code].get("lat") is None and plane.get("lat") is not None:
                    planes[hex_code]["lat"] = plane["lat"]
                    planes[hex_code]["lon"] = plane["lon"]

                    if not planes[hex_code].get("alt"):
                        planes[hex_code]["alt"] = plane["alt"]
                    if not planes[hex_code].get("hdg"):
                        planes[hex_code]["hdg"] = plane["hdg"]

                    planes[hex_code]["source"] = "adsb.fi + FR24 (Pos)"



        logger.info(f"Fetched {len(planes)} planes total")
        for hex_code, plane in planes.items():
            process_target(hex_code, plane)

        time.sleep(CFG.poll_interval_sec)


if __name__ == "__main__":
    main()