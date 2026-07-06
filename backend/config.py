from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Sistema Inteligente de Detección de Vehículos Estacionados"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/vehicle_detection"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # WhatsApp (Evolution API)
    WHATSAPP_API_URL: str = "http://localhost:8080"
    WHATSAPP_API_KEY: str = ""
    
    # AI Services
    YOLO_MODEL_PATH: str = "models/yolov8n.pt"
    OCR_LANGUAGES: list = ["en"]
    
    # File paths
    UPLOAD_DIR: str = "uploads"
    IMAGE_DIR: str = "uploads/images"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()