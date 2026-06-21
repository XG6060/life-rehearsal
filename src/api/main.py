"""FastAPI 应用入口

启动方式：
    uvicorn src.api.main:app --reload
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.api.middleware import CORSMiddleware, RequestLoggingMiddleware
from src.api.routes.analyze import router as analyze_router
from src.db.database import close_database, init_database
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_database()
    yield
    await close_database()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# 挂载静态文件目录（供 Three.js 加载 3D 模型）
_static = Path(__file__).resolve().parent.parent.parent / "ui" / "static"
_static.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static)), name="static")

app.add_middleware(CORSMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(analyze_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
