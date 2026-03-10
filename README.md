## Military High Value Asset Tracker
A Python based tool to track strategic military movements in Real Time and conveniently send Alerts to a Discord channel.

## Features
* **Dual-Api Data Fusion**
* **Smart Filtering** Recognizes real strategic movements based on altitude and time intervals.
* **Anti-Spam Mechanism** Tracks planes in local storage to prevent duplicate alerts.
* **Training Mode** Optional mode in the configuration, to also track domestic- and training flights.

## Supported Plane Types
* **Boeing E6-B Mercury**
* **Boeing RC-135 Rivet Joint**
* **Boeing VC-25 Air Force 1**
* **Boeing C-32A Air Force 2**
* **Boeing E-3A Sentry**
* **Northrop B-2 Spirit**
* **Boeing E-4B Nightwatch**
* **Northrop Grumman RQ-4 Global Hawk**
* **Lockheed U-2 Dragon Lady**
* **Boeing B-52 Stratofortress**
* **Rockwell B-1 Lancer**
* **Boeing KC-135 Stratotanker**
* **General Atomics MQ-9 Reaper**
* **Boeing P-8A Poseidon**
* **Northrop Grumman MQ-4C Triton**
* **Bell Boeing V-22 Osprey**
* **Lockheed Martin F-35 Lightning II**
* **Lockheed Martin F-22 Raptor**
* **Eurofighter Typhoon**

## Installation and Setup
1. Clone the repository
```bash
git clone https://github.com/davidc1907/military-flight-tracker.git
cd military-flight-tracker
```

2. Install the requirements
```bash
pip install -r requirements.txt
```
3. Rename .env.example to .env and fill in the required API keys and Discord webhook URL.
4. Set Training mode to True if you want to track domestic and training flights.
5. Run the script
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