import os
import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

engine = create_engine(DATABASE_URL)
Base = declarative_base()


def get_password_hash(password: str):
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be 72 bytes or less.")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str):
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
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


class MemoUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    memos = []
    if username:
        memos = db.query(Memo).order_by(Memo.id.desc()).limit(3).all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"username": username, "memos": memos},
    )


@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None})


@app.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        new_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return RedirectResponse("/login", status_code=303)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "signup.html",
            {"error": "이미 사용 중인 아이디 또는 이메일입니다."},
        )


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        request.session["username"] = user.username
        return RedirectResponse("/memos", status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "아이디 또는 비밀번호가 올바르지 않습니다."},
    )


@app.get("/logout")
def logout(request: Request):
    request.session.pop("username", None)
    return RedirectResponse("/", status_code=303)


@app.get("/memos")
def read_memos(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return RedirectResponse("/login", status_code=303)

    memos = db.query(Memo).order_by(Memo.id.desc()).all()
    return templates.TemplateResponse(
        request,
        "memos.html",
        {"memos": memos, "username": username},
    )


@app.post("/memos")
def create_memo(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("username"):
        return RedirectResponse("/login", status_code=303)

    new_memo = Memo(title=title, content=content)
    db.add(new_memo)
    db.commit()
    db.refresh(new_memo)
    return RedirectResponse("/memos", status_code=303)


@app.put("/memos/{item_id}")
def update_memo(item_id: int, memo: MemoUpdate, db: Session = Depends(get_db)):
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


@app.post("/memos/{item_id}/delete")
def delete_memo(item_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("username"):
        return RedirectResponse("/login", status_code=303)

    db_memo = db.query(Memo).filter(Memo.id == item_id).first()

    if db_memo is not None:
        db.delete(db_memo)
        db.commit()

    return RedirectResponse("/memos", status_code=303)
