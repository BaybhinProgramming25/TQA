from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

from classes.userdata import LoginData, SignUpData

router = APIRouter()
load_dotenv()

# Add health endpoint
@router.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Login endpoint
@router.post("/api/login")
async def login(data: LoginData):

    # data already becomes LoginData(email=email, passworwd=password)
    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")
    
    # More to be implemented 
    pass 



@router.post("/api/signup")
async def signup(data: SignUpData):

    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters long")
    
    # More to be implemented
    pass 