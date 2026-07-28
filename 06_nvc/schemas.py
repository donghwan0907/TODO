from pydantic import BaseModel
from typing import Optional

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
    username: str
    password: str