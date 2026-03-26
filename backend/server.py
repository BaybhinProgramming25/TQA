from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from controllers.user import router as user_router
from controllers.documents import router as documents_router
from controllers.qa import router as qa_router
from database.database import engine, Base
from helpers.limiter import limiter
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("../mysql-data", exist_ok=True) 
    os.makedirs("/uploads", exist_ok=True)   
    os.makedirs("data", exist_ok=True)  
    Base.metadata.create_all(bind=engine)
    yield 

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = ["http://localhost:5173"]

codespace_name = os.environ.get("CODESPACE_NAME")
if codespace_name:
    origins.append(f"https://{codespace_name}-5173.app.github.dev")

# For development purposes, create these settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Cookie"]
)

app.include_router(qa_router)
app.include_router(user_router)
app.include_router(documents_router)

