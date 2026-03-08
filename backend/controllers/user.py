from fastapi import APIRouter, HTTPException, Depends 
from dotenv import load_dotenv
from classes.userdata import LoginData, SignUpData
from sqlalchemy.orm import Session
from backend.database.models import User 
from backend.database.database import get_db

import bcrypt 

router = APIRouter()
load_dotenv()

# Add health endpoint
@router.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Login endpoint
@router.post("/api/login")
async def login(data: LoginData, db: Session = Depends(get_db)):

    # Check JWT

    # Business logic checks 

    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")

    try:
        user = db.query(User).filter(User.email == data.email).first()

        if not user:
            raise HTTPException(status_code=404, detail="Email not found")
            
        if not bcrypt.verify(user.password, data.password):
            raise HTTPException(status_code=401, detail="Invalid Password")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

@router.post("/api/signup")
async def signup(data: SignUpData):

    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")
    
    # More to be implemented
    pass 