from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="DeepAudit Lite",
    description="本地优先的安全审计平台 - 离线特征匹配 + 在线AI增强",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "DeepAudit Lite",
        "version": "1.0.0",
        "description": "本地优先的安全审计平台"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
