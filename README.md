# Project Corvus – Military High Value Asset Tracker

Python tool for real-time tracking of strategic military flights. Fuses multiple ADS-B sources, applies score-based filtering, and pushes alerts via Discord webhooks or the optional slash-command bot.

## Features
- Multi-source fusion: `adsb.fi` military feed, OpenSky (auth, Atlantic bounding box), and FlightRadar24; positions/altitude merged when available.
- Scoring & hotzones: Altitude, heading stability, direct or projected hotzone entries (configurable in `config.py`).
- VIP detection: Known ICAO hex codes from `constants.py` trigger prioritized alerts.
- Anti-spam: Per-hex cooldown and score deltas (`core.history`) to avoid duplicates.
- Training mode: Toggle `TRAINING_MODE` to include all flights or only strategic/VIP.
- Geocoding: Rough country lookup via `reverse_geocode`.
- Discord delivery: Webhook alerts from `main.py`; slash-command bot (`discord_bot.py`) with per-channel subscriptions and field selection.

## Supported Aircraft
- Boeing E6-B Mercury
- Boeing RC-135 Rivet Joint
- Boeing VC-25 Air Force 1
- Boeing C-32A Air Force 2
- Boeing E-3A Sentry
- Northrop B-2 Spirit
- Boeing E-4B Nightwatch
- Northrop Grumman RQ-4 Global Hawk
- Lockheed U-2 Dragon Lady
- Boeing B-52 Stratofortress
- Rockwell B-1 Lancer
- Boeing KC-135 Stratotanker
- General Atomics MQ-9 Reaper
- Boeing P-8A Poseidon
- Northrop Grumman MQ-4C Triton
- Bell Boeing V-22 Osprey
- Lockheed Martin F-35 Lightning II
- Lockheed Martin F-22 Raptor
- Eurofighter Typhoon

## Requirements
- Python 3.11+
- Credentials: OpenSky `OPENSKY_USER` / `OPENSKY_SECRET` (for position data), Discord `WEBHOOK_URL`; optional Discord `BOT_TOKEN` for slash commands.
- Install deps:

```bash
pip install -r requirements.txt
```

## Configuration (.env)
Create a `.env` in the project root or export the variables:

```
OPENSKY_USER=your_opensky_user
OPENSKY_SECRET=your_opensky_pass
WEBHOOK_URL=https://discord.com/api/webhooks/...
TRAINING_MODE=false
BOT_TOKEN=your_discord_bot_token_optional
```

Adjust altitudes, headings, hotzones, and polling intervals in `config.py` as needed.

## Usage
- Start webhook tracker (alerts to `WEBHOOK_URL`):

```bash
python main.py
```
6. Enjoy!

## Credits
* **OpenSky API by OpenSkyNetwork** https://opensky-network.org/
* **adsb.fi API by adsb.fi** https://adsb.fi/

## Important Notes
This project is not affiliated with OpenSkyNetwork or adsb.fi in any way.
This project is for educational and informational purposes only. It only uses publicly accessible and unencrypted ADS-B data. The author is not responsible for any misuse of the tool or any consequences that may arise from its use. Always respect privacy and legal boundaries when tracking aircraft.

## Data Sources
- adsb.fi Military Feed
- OpenSky Network (Atlantic bounding box, auth required)
- FlightRadar24 API (position/altitude enrichment)

## Notes
This project uses only publicly available ADS-B data. No affiliation with OpenSkyNetwork, adsb.fi, or FlightRadar24. Use at your own risk; comply with local laws and privacy expectations.
