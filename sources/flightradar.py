from FlightRadar24 import FlightRadar24API
import logging
from constants import TARGET_TYPES

logger = logging.getLogger(__name__)
fr_api = FlightRadar24API()

def fetch_flightradar():
    planes = {}
    try:
       flights = fr_api.get_flights()

       for f in flights:
           if f.aircraft_code not in TARGET_TYPES:
               continue

           hex_code = f.icao_24bit.lower() if f.icao_24bit else None
           if not hex_code:
               continue

           planes[hex_code] = {
               "alt": f.altitude,
               "hdg": f.heading,
               "lat": f.latitude,
               "lon": f.longitude,
               "flight": f.aircraft_code,
               "type": f.aircraft_code,
               "reg": f.registration,
               "squawk": f.squawk,
               "source": "FR24"
              }

    except Exception as e:
        logger.error(f"Error fetching flightradar: {e}")

    return planes
