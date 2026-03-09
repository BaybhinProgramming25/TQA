from sqlalchemy import Column, Integer, String 
from database.database import Base

class User(Base):
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(100))
    lastname = Column(String(100))
    email = Column(String(50), unique=True)
    password = Column(String(20))