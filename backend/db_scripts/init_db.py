"""
Initial database setup script.
Creates initial data like default configurations and admin user.
"""
from sqlalchemy.orm import Session
from ..database import SessionLocal, engine
from ..models.base import Base
from ..models.user import User
from ..models.config import SystemConfig
from ..utils.security import get_password_hash
import json

def init_db() -> None:
    """Initialize database with default data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create default system configurations if they don't exist
        default_configs = [
            {
                "key": "parking_time_threshold",
                "value": "300",  # 5 minutes in seconds
                "description": "Time in seconds to consider a vehicle as parked",
                "data_type": "integer"
            },
            {
                "key": "working_hours_start",
                "value": "08:00",
                "description": "Start of working hours (HH:MM format)",
                "data_type": "string"
            },
            {
                "key": "working_hours_end",
                "value": "18:00",
                "description": "End of working hours (HH:MM format)",
                "data_type": "string"
            },
            {
                "key": "whatsapp_enabled",
                "value": "true",
                "description": "Enable WhatsApp notifications",
                "data_type": "boolean"
            },
            {
                "key": "default_whatsapp_numbers",
                "value": "[]",
                "description": "Default WhatsApp numbers for notifications",
                "data_type": "json"
            },
            {
                "key": "yolo_confidence_threshold",
                "value": "0.5",
                "description": "Confidence threshold for YOLO detections",
                "data_type": "string"
            },
            {
                "key": "ocr_confidence_threshold",
                "value": "0.6",
                "description": "Confidence threshold for OCR detections",
                "data_type": "string"
            }
        ]
        
        for config_data in default_configs:
            existing_config = db.query(SystemConfig).filter(
                SystemConfig.key == config_data["key"]
            ).first()
            
            if not existing_config:
                config = SystemConfig(**config_data)
                db.add(config)
        
        # Create admin user if it doesn't exist
        admin_email = "admin@vehicledetection.local"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                username="admin",
                hashed_password=get_password_hash("admin123"),  # Change in production!
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            db.add(admin_user)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()