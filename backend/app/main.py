import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.logger import get_logger
from app.routes import auth_router, lms_router
from app.services.demo_seed import seed_demo

settings = get_settings()
logger = get_logger(__name__)

# Create all database tables
Base.metadata.create_all(bind=engine)

cors_origins = os.getenv("CORS_ORIGINS")
allowed_origins = (
    [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    if cors_origins is not None
    else ["http://localhost:5173", "http://localhost:3000"]
)


def _start_demo_seed_on_startup() -> bool:
    enabled = os.getenv("SEED_DEMO_ON_START", "").strip().lower() == "true"
    tutor_password = os.getenv("DEMO_TUTOR_PASSWORD", "")
    student_password = os.getenv("DEMO_STUDENT_PASSWORD", "")
    if not enabled or not tutor_password or not student_password:
        logger.info("Demo seeding is disabled")
        return False

    def run_seed() -> None:
        try:
            stored_count = seed_demo()
            logger.info(
                "Background demo seeding completed (vectors=%s)",
                stored_count,
            )
        except Exception as error:
            logger.error(
                "Background demo seeding failed; application will continue (%s)",
                type(error).__name__,
            )

    try:
        threading.Thread(
            target=run_seed,
            name="demo-seed",
            daemon=True,
        ).start()
    except Exception as error:
        logger.error(
            "Background demo seeding could not start; application will continue (%s)",
            type(error).__name__,
        )
        return False

    logger.info("Background demo seeding started")
    return True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _start_demo_seed_on_startup()
    yield


# Create FastAPI app
app = FastAPI(
    title="Tutor LMS API",
    description="A full-stack LMS platform for tutors and students",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(lms_router)


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/health", tags=["health"])
async def health_check_full():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Tutor LMS API in {settings.environment} mode")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )
