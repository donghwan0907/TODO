from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from database import Base

class Memo(Base):
    __tablename__ = "memos"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True) 
    username = Column(String, unique=True, index=True) 
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)