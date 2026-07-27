import os
import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

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

app.add_middleware(SessionMiddleware, secret_key="secret-key")

class Memo(Base):
    __tablename__ = "memos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True) 
    username = Column(String, unique=True, index=True) 
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class MemoCreate(BaseModel):
    title: str
    content: str

class MemoUpdate(BaseModel): 
    title: Optional[str] = None
    content : Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str 
    password: str

class UserLogin(BaseModel):
    username:str
    password:str

def get_db():
    db = Session(bind=engine)
    try: 
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root(request: Request): 
    return templates.TemplateResponse(request, "home.html")

# 회원가입
@app.post("/signup")
def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        username=signup_data.username, 
        email = signup_data.email, 
        hashed_password = get_password_hash(signup_data.password)
    )
    db.add(new_user)
    db.commit() 
    db.refresh(new_user) 
    return new_user
   
# 로그인
@app.post("/login")
def login(
    request: Request, signin_data: UserLogin, db: Session=Depends(get_db)
):
    user = db.query(User).filter(User.username==signin_data.username).first()    
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"]=user.username
        print(request.session)
        return{"message":"로그인 성공"}

@app.post("/memos")
def create_memo(memo: MemoCreate, db: Session = Depends(get_db)):
    new_memo = Memo(title=memo.title, content=memo.content)
    db.add(new_memo)
    db.commit()
    db.refresh(new_memo)
    return new_memo

#로그아웃
@app.post("/logout")
def logout(request: Request):
    request.session.pop("username",None)
    print(request.session)
    return{
        "message":"로그아웃 되었습니다."
    }


# 메모조회
@app.get("/memos")
def read_memos(db: Session = Depends(get_db)):
    memos = db.query(Memo).all()
    return [
        {"title": memo.title, "content": memo.content} for memo in memos
    ]

# 메모수정
@app.put("/memos/{item_id}")
def update_memo(item_id: int, memo:MemoUpdate, db: Session = Depends(get_db)):
    db_memo = db.query(Memo).filter(Memo.id == item_id).first()

    if db_memo is None:
        return {"error": "메모를 찾을 수 없습니다."}

    if memo.title is not None:
        db_memo.title = memo.title
    if memo.content is not None:
        db_memo.content = memo.content

    db.commit()
    db.refresh(db_memo)

    return db_memo


# 메모삭제
@app.delete("/memos/{item_id}")
def delete_memo(item_id: int, db: Session = Depends(get_db)):
    db_memo = db.query(Memo).filter(Memo.id == item_id).first()

    if db_memo is None:
        return {
            "error" : "메모를 찾을 수 없습니다."
        }

    db.delete(db_memo)
    db.commit()

    return {
        "message": "메모를 삭제했습니다"
    }