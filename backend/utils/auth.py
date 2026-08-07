from sqlalchemy.orm import Session
from models.user import User
from utils.security import verify_password

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_active_user():
    # This will be implemented in the routers as a dependency
    pass