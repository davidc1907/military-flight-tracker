import time
from core.history import flight_history
from config import CFG
import math


def check_profile(hex_code, alt, hdg, lat, lon, plane):
    # Score incoming plane based on altitude, heading stability, and hotzone checks
    score = 0
    now = time.time()

    if CFG.training_mode:
        return True

    if hex_code not in flight_history:
        flight_history[hex_code] = {
            "alt": alt,
            "hdg": hdg,
            "time": now,
            "last_alert": 0,
            "last_score": 0,
            "alerted_score": 0
        }

    prev = flight_history[hex_code]
    time_tracked = now - prev["time"]
    hdg_diff = abs(hdg - prev["hdg"])
    hdg_diff = min(hdg_diff, 360 - hdg_diff)

    # Gate 1: Altitude weight
    if alt > 28000:
        score += 25
    elif alt > 20000:
        score += 15

    # Gate 2: Heading stability within window
    if hdg_diff > CFG.stable_hdg_delta:
        prev["hdg"] = hdg
        prev["time"] = now
    else:
        if time_tracked >= CFG.stable_hdg_window_sec:
            score += 25
            prev["time"] = now

    in_hotzone = False

    # Gate 3a: Direct hotzone hit
    if lat is not None and lon is not None:
        for zone in CFG.HOTZONES:
            try:
                lat_min, lat_max, lon_min, lon_max = zone

                if any(v is None for v in (lat_min, lat_max, lon_min, lon_max)):
                    continue

                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    score += 30
                    in_hotzone = True
                    break
            except (TypeError, ValueError):
                continue

    # Gate 3b: Projected hotzone entry
    if not in_hotzone and lat is not None and lon is not None:
        hdg_rad = math.radians(hdg)

        step_lat = math.cos(hdg_rad) * 0.5
        step_lon = (math.sin(hdg_rad) * 0.5) / max(0.1, math.cos(math.radians(lat)))

        trajectory_hit = False

        for i in range(1, 21):
            proj_lat = lat + step_lat * i
            proj_lon = lon + step_lon * i

            for zone in CFG.HOTZONES:
                zone_lat_min, zone_lat_max, zone_lon_min, zone_lon_max = zone
                if zone_lat_min <= proj_lat <= zone_lat_max and zone_lon_min <= proj_lon <= zone_lon_max:
                    trajectory_hit = True
                    break

            if trajectory_hit:
                score += 20
                break

    old_score = prev.get("last_score", 0)
    prev["last_score"] = score

    # Gate 4: Threshold and deduplication
    proceed_to_gate_4 = False
    threshold = 40 if in_hotzone else 70

    if score >= 80:
        proceed_to_gate_4 = True
    elif threshold <= score <= 79:
        if score > old_score:
            proceed_to_gate_4 = True
        else:
            return False
    else:
        return False

    if proceed_to_gate_4:
        time_since_last_alert = now - prev.get("last_alert", 0)
        score_diff = score - prev.get("alerted_score", 0)

        cooldown_ok = time_since_last_alert > CFG.alert_cooldown_sec
        score_jump_ok = score_diff > 15

        if cooldown_ok or score_jump_ok:
            prev["last_alert"] = now
            prev["alerted_score"] = score

            return score

    return False