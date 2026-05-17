import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database import init_db
from backend.services.model_loader import load_models
import backend.services.model_loader as ml
from backend.routers import upload, manual, results, jobs, dashboard, live

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Loading models...")
    load_models()
    yield
    # Stop live monitor cleanly on shutdown
    from backend.services import live_monitor_service
    if live_monitor_service._state.get("running"):
        logger.info("Stopping live monitor on shutdown...")
        await live_monitor_service.stop_monitor()
    logger.info("Shutting down.")


app = FastAPI(
    title="LogDetAction API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router,     prefix="/api/analyze",   tags=["analyze"])
app.include_router(manual.router,     prefix="/api/analyze",   tags=["analyze"])
app.include_router(results.router,    prefix="/api/results",   tags=["results"])
app.include_router(jobs.router,       prefix="/api/jobs",      tags=["jobs"])
app.include_router(dashboard.router,  prefix="/api/dashboard", tags=["dashboard"])
app.include_router(live.router,       prefix="/api/live",      tags=["live"])


@app.get("/api/health", tags=["health"])
async def health():
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if ml.model_loaded:
        return {
            "status": "ok",
            "model_loaded": True,
            "device": device,
            "load_timings": ml.load_timings,
        }
    return JSONResponse(
        status_code=503,
        content={
            "status": "degraded",
            "model_loaded": False,
            "device": device,
            "error": ml.model_error or "Model not loaded.",
        },
    )
