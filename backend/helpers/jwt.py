# All the JWT logic will be added here 
from datetime import datetime, timedelta, timezone

import os, jwt


def create_jwt_token(user_id: str):

    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1) # Token expires in 1 hour
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")


def decode_jwt_token():
    pass 
    # More to be implemented 