from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

load_dotenv()
import os, jwt

ALGORITHM = "SHA256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
oauth2_sceme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_sceme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or Expired JWT token. Please log in again.")
    return payload


def create_token(data: dict) -> str:

    global JWT_SECRET_KEY, ALGORITHM
    
    to_encode = data.copy()
    expire = datetime.now(datetime.time) + timedelta(hours=1) # Token expries in 1 hour 
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token 

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload 
    except:
        return None # Invalid JWT token provided 