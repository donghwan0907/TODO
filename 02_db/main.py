import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")


app=FastAPI()
templates=Jinja2Templates(directory="templates")


engine=create_engine(DATABASE_URL)
Base=declarative_base()

class Memo(Base):
    __tablename__="memos"
    id=Column(Integer, primary_key=True, index=True)
    title=Column(String)
    content=Column(String)

class MemoCreate(BaseModel):
    title:str
    content:str

class MemoUpdate(BaseModel):
    title: Optional[str]=None
    content: Optional[str]=None

def get_db():
    db=Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request, "home.html")

@app.post("/memos")
def create_memo(memo:MemoCreate, db:Session=Depends(get_db)):
    new_memo=Memo(title=memo.title, content=memo.content)
    db.add(new_memo)
    db.commit()
    db.refresh(new_memo)
    return new_memo

#메모 조회하기
@app.get("/memos")
def read_memos(db:Session=Depends(get_db)):
    memos=db.query(Memo).all()
    return {
        memo.title for memo in memos
    }

#메모수정
@app.put("/memos/{item_id}")
def update_memo(item_id:int, memo:MemoUpdate, db:Session=Depends(get_db)):
    db_memo=db.query(Memo).filter(Memo.id==item_id).first()

    if db_memo is None:
        return {"error":"메모를 찾을 수 없습니다."}
    if memo.title is not None:
        db_memo.title=memo.title
    if memo.content is not None:
        db_memo.content=memo.content


    db.commit()
    db.refresh(db_memo)

    return db_memo

#메모 삭제
@app.delete("/memos/{item_id}")
def delete_memo(item_id:int, db:Session=Depends(get_db)):
    db_memo=db.query(Memo).filter(Memo.id==item_id).first()

    if db_memo is None:
        return {"error":"메모를 찾을 수 없습니다."}

    db.delete(db_memo)
    db.commit()

    return{
        "message":"메모를 삭제했습니다."
    }

