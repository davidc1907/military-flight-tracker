import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    opensky_user: str = os.getenv("OPENSKY_USER", "")
    opensky_pass: str = os.getenv("OPENSKY_SECRET", "")
    webhook_url: str = os.getenv("WEBHOOK_URL", "")
    google_geo_api: str = os.getenv("GOOGLE_GEO_API", "")
    training_mode: bool = os.getenv("TRAINING_MODE", "false").lower() == "true"

    alert_cooldown_sec: int = 7200
    history_ttl_sec: int = 86400
    poll_interval_sec: int = 60

    min_alt_training_ft: int = 10000
    min_alt_normal_ft: int = 28000

    hdg_min: int = 45
    hdg_max: int = 160

    stable_hdg_delta: float = 10.0
    stable_hdg_window_sec: int = 240

    bbox_atlantic: tuple = (30.0, 60.0, -70.0, 40.0)

    atlantic_lon_threshold: float = -10.0
    europe_lon_threshold: float = 5.0

    me_hdg_min: int = 100
    me_hdg_max: int = 160


CFG = Config()