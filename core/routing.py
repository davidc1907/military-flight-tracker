from typing import Optional
from config import CFG


def estimate_route(lon: Optional[float], hdg: Optional[float]) -> str:
    """
    Estimate the likely mission route based on longitude and heading.

    Returns a human-readable route classification string.
    """

    if lon is None or hdg is None:
        return "Route: Position unknown"

    # Aircraft still over the western Atlantic moving east
    if lon < CFG.atlantic_lon_threshold:
        return "Route: Transatlantic (West → East)"

    # Aircraft already over Europe heading toward the Middle East
    if lon > CFG.europe_lon_threshold and CFG.me_hdg_min <= hdg <= CFG.me_hdg_max:
        return "Route: Middle East Deployment (Europe → Middle East)"

    # Default classification
    return "Route: Strategic Movement"