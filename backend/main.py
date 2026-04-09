import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import run, chat
from backend.services.session import start_cleanup_task

SESSION_EXPIRY = int(os.environ.get("SESSION_EXPIRY_MINUTES", "120"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_cleanup_task(SESSION_EXPIRY)
    yield


app = FastAPI(title="Socratic Debugging Tutor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(run.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
