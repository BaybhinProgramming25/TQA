from pydantic import BaseModel 

class LoginData(BaseModel):
    email: str 
    password: str 

class SignUpData(BaseModel):
    email: str 
    password: str 
    age: int 
    # More fields to be determined 
