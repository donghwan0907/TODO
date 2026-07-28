import bcrypt
from sqlalchemy.orm import Session
from database import engine

# 비밀번호 생성 함수 
def get_password_hash(password: str):
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72: 
        raise ValueError("Password must be 72 bytes or less.")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

# 비밀번호 검증 
def verify_password(plain_password: str, hashed_password: str): 
    try: 
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except ValueError: 
        return False

def get_db():
    db = Session(bind=engine)
    try: 
        yield db
    finally:
        db.close()