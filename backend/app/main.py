import logging
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.routes import (
    ai,
    auth,
    billing,
    brand_kit,
    content,
    dashboard,
    planner,
    profile,
    repurpose,
    seo,
    templates,
)
from backend.app.services.seed_service import SeedService

# Setup structured server-side logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("contently.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup initialization and shutdown cleanup."""
    logger.info("Initializing Contently Backend Engine...")

    # Create tables if not present
    Base.metadata.create_all(bind=engine)

    # Ensure OAuth columns exist on users table
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "oauth_provider" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50)"))
                if "oauth_id" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(255)"))
        logger.info("Database schemas and OAuth columns verified.")
    except Exception as e:
        logger.warning("OAuth column migration check note: %s", str(e))

    # Seed initial demo user and data
    db = SessionLocal()
    try:
        SeedService.seed_initial_data(db)
        logger.info("Initial demo seed verified for '%s'.", settings.DEMO_USER_EMAIL)
    except Exception as e:
        logger.error("Error during initial data seed: %s", str(e), exc_info=True)
    finally:
        db.close()

    yield
    logger.info("Contently Backend Engine shutdown complete.")


app = FastAPI(
    title="Contently AI Content Platform API",
    description="Production-grade API for Contently AI Content Creation & Distribution Platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Safe CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format input validation errors into clear structured responses."""
    formatted_errors = []
    for err in exc.errors():
        field_name = " -> ".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({
            "field": field_name,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error"),
        })
    logger.warning("Validation failed for %s %s: %s", request.method, request.url.path, formatted_errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "detail": "Input validation failed. Please check the submitted fields.",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled errors and return structured 500 without crashing."""
    logger.error("Unhandled internal error at %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "detail": "An internal server error occurred. Our engineering team has logged this event.",
        },
    )


# Health & Readiness Check Endpoints
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify server status and database connectivity."""
    db_status = "connected"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        db_status = f"unhealthy: {e!s}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": "contently-ai-backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# Include Application Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(content.router)
app.include_router(ai.router)
app.include_router(templates.router)
app.include_router(brand_kit.router)
app.include_router(planner.router)
app.include_router(repurpose.router)
app.include_router(seo.router)
app.include_router(profile.router)
app.include_router(billing.router)


@app.get("/", tags=["Root"])
def root_status():
    return {
        "message": "Contently AI Content Platform API is running.",
        "docs": "/docs",
        "health": "/health",
    }
