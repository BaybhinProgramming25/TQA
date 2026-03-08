from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from controllers.user import router as user_router
from backend.database.database import engine, get_db, Base
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("../mysql-data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print('Tables Created!')
    yield 

app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173"]

codespace_name = os.environ.get("CODESPACE_NAME")
if codespace_name:
    origins.append(f"https://{codespace_name}-5173.app.github.dev")

# For development purposes, create these settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# app.include_router(qa_router)
app.include_router(user_router)

