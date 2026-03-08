from dotenv import load_dotenv

from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, declarative_base 


load_dotenv()
import os 

# SPECIFY database url
DATABASE_URL= os.getenv("DATABASE_URL")

# Make the engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Gives a database session to each request 
def get_db():
    db = SessionLocal()
    try:
        yield db 
    except:
        db.close()


