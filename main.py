import time
import logging

from utils.logging_setup import setup_logging
from sources.adsbfi import fetch_adsbfi
from sources.opensky import fetch_opensky

from core.tracker import check_profile
from core.history import cleanup

from services.discord import send_discord_alert

from config import CFG

setup_logging()

logger = logging.getLogger(__name__)

def main():

    logger.info("Tracker started")

    while True:

        cleanup()

        planes = {}
        planes.update(fetch_adsbfi())
        planes.update(fetch_opensky())

        for hex_code, plane in planes.items():

            if check_profile(hex_code, plane["alt"], plane["hdg"]):

                msg = f"🚨 Strategic Aircraft: {hex_code}"
                send_discord_alert(msg)

        time.sleep(CFG.poll_interval_sec)


if __name__ == "__main__":
    main()