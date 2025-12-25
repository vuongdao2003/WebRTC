import os
from typing import Optional

# Try to load a local .env file if python-dotenv is installed. This makes
# running test scripts easier without requiring manual env setup.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
import os
from typing import Optional


class Settings:
    """Simple settings container reading from environment variables.

    Using plain os.environ avoids pydantic BaseSettings version issues.
    """
    ROBOFLOW_API_KEY: Optional[str]
    ROBOFLOW_MODEL: Optional[str]
    LOCAL_YOLO_MODEL: str
    DETECT_IMG_SIZE: int

    def __init__(self):
        self.ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
        self.ROBOFLOW_MODEL = os.getenv("ROBOFLOW_MODEL")
        self.LOCAL_YOLO_MODEL = os.getenv("LOCAL_YOLO_MODEL", "models/yolov8n.pt")
        try:
            self.DETECT_IMG_SIZE = int(os.getenv("DETECT_IMG_SIZE", "640"))
        except Exception:
            self.DETECT_IMG_SIZE = 640
        # Database connection settings (for MySQL)
        # Preferred: set DATABASE_URL or individual vars below in be/.env
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
        self.DB_PORT = int(os.getenv("DB_PORT", "3306"))
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASS = os.getenv("DB_PASS")
        self.DB_NAME = os.getenv("DB_NAME", "RTC_AI_DB")
        # optional schema (MySQL schema == database by default). If you want a schema prefix, set this.
        self.DB_SCHEMA = os.getenv("DB_SCHEMA", "realtime_ai_system")


settings = Settings()
