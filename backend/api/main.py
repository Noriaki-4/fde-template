from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from backend.config import get_config
from backend.api.routes import health, search
from backend.database.db import init_db

logger = structlog.get_logger()

config = get_config()
app = FastAPI(
    title="FDE Template API",
    description="FDE Modular AI PoC Platform",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(search.router, prefix="/search", tags=["search"])

@app.on_event("startup")
async def startup_event():
    logger.info("Backend startup", config=config.model_dump())
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
