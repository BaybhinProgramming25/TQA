from dotenv import load_dotenv
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, DeclarativeBase 

load_dotenv(interpolate=True, override=True)
import os 

DATABASE_URL= os.getenv("DATABASE_URL")
print(DATABASE_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass 

def get_db():
    db = SessionLocal()
    try:
        yield db 
    except:
        db.close()


