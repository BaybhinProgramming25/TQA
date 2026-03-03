import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.database import connect_mongo, close_mongo

from controllers.qa import router as qa_router
from controllers.user import router as user_router

@asynccontextmanager
async def lifespan(app):
    await connect_mongo()
    yield
    await close_mongo()

app = FastAPI()

origins = [
    "http://localhost:5173",
]

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

app.include_router(qa_router)
app.include_router(user_router)

