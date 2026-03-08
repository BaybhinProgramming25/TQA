from sqlalchemy import Column, Integer, String 
from database import Base


class User(Base):
    
    # specify the tablename users 
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    password = Column(String(100))