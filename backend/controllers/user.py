from fastapi import APIRouter, HTTPException, Depends 
from fastapi.responses import JSONResponse

from dotenv import load_dotenv

from classes.userdata import LoginData, SignUpData
from sqlalchemy.orm import Session

from database.models import User 
from database.database import get_db

from helpers.jwt import create_token
from helpers.hashing import hash_password, verify_password

router = APIRouter()
load_dotenv()


@router.post("/api/login")
def login(data: LoginData, db: Session = Depends(get_db)):

    try:
        user = db.query(User).filter(User.email == data.email).first()

        if not user:
            raise HTTPException(status_code=404, detail="Email not found")
        
        if not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid Password")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error {e}")


    token = create_token({"username": data.email})
    
    response = JSONResponse(
        content={"message": "Logged In!"},
        status_code=200
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True, # JavaScript can't alter this cookie
        secure=True, # send only over HTTPS
        samesite="lax",
        max_age=3600
    )
    return response

@router.post("/api/logout")
def logout():
    response = JSONResponse(content={"message": "Logged out"}, status_code=200)
    response.delete_cookie(key="access_token", httponly=True, secure=True, samesite="lax")
    return response


@router.post("/api/signup")
def signup(data: SignUpData, db: Session = Depends(get_db)):

    email_exists = db.query(User).filter(User.email == data.email).first()
    if email_exists:
        raise HTTPException(status_code=409, detail="Email already exists")
    
    hashed_password = hash_password(data.password)

    new_user = User(
        firstname=data.firstname,
        lastname=data.lastname,
        email=data.email,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_token({"username": data.email})

    response = JSONResponse(
        content={"message": "Account Created!"},
        status_code=200
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )

    return response 
    
