from pydantic import BaseModel, EmailStr 

class LoginData(BaseModel):
    email: EmailStr
    password: str 

class SignUpData(BaseModel):
    email: EmailStr
    password: str 
    age: int 
