from http.client import HTTPException

from fastapi import APIRouter, Response, Depends
from dotenv import load_dotenv

import jwt

router = APIRouter()
load_dotenv()

# Add health endpoint
@router.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Login endpoint
@router.post("/api/login")
async def login(data: LoginData, response: Response):

    email = data.email.strip().lower()
    password = data.password.strip()

    # Check to see if password length is at least 8 characters
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    # Then check to see if email already exists in the database
    
    
    """
    users_collection = get_users_collection()
    user = users_collection.find_one({"email": data.email})
    
    if not user:
        return {"error": "Invalid email or password"}
    
    if not bcrypt.checkpw(data.password.encode('utf-8'), user['password']):
        return {"error": "Invalid email or password"}
    
    # Generate JWT token
    payload = {
        "user_id": str(user['_id']),
        "exp": datetime.now(timezone.utc) + timedelta(days=7)  # Token expires in 7 days
    }
    token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    
    # Set token in cookie
    response.set_cookie(key="token", value=token, httponly=True, samesite='Lax')
    
    return {"message": "Login successful", "user_data": {"email": user['email'], "name": user['name']}}
    """