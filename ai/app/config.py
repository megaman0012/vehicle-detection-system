import os
from pathlib import Path


class Settings:
    """Runtime settings for the AI service, read from environment variables."""

    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")
    BACKEND_USERNAME: str = os.getenv("BACKEND_USERNAME", "admin")
    BACKEND_PASSWORD: str = os.getenv("BACKEND_PASSWORD", "admin123")
    MODEL_PATH: Path = Path(os.getenv("MODEL_PATH", "/app/models"))
    DEVICE: str = os.getenv("DEVICE", "cpu")

    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", "2"))
    PARKING_TIME_THRESHOLD: int = int(os.getenv("PARKING_TIME_THRESHOLD", "300"))
    REPORT_INTERVAL: float = float(os.getenv("REPORT_INTERVAL", "10"))


settings = Settings()
