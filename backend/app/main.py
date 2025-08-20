# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from .db import get_db
from .config import Base, engine
from .routes import auth  # make sure backend/app/routes/auth.py defines `router`

APP_NAME = os.getenv("APP_NAME", "DTMS Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
ENV = os.getenv("ENV", "development")

# Comma-separated origins: e.g. "http://localhost:5173,https://yourdomain.com"
_frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _frontend_origins.split(",") if o.strip()]

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Daily Task Management System – API",
    contact={"name": "DTMS", "url": "https://github.com/rahkaf/Daily_Task_Management_System"},
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"] if ENV == "development" else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Startup / Shutdown ----
@app.on_event("startup")
def on_startup():
    # Create tables for the current SQLAlchemy metadata (SQLite dev; replace when moving to Neo4j layer)
    Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
def on_shutdown():
    # Nothing to close explicitly because we use scoped sessions via dependency
    pass

# ---- Routers ----
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# ---- Core Endpoints ----
@app.get("/", tags=["Meta"])
def root():
    return {
        "message": "✅ DTMS API is live",
        "env": ENV,
        "version": APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }

@app.get("/healthz", tags=["Meta"])
def healthz(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))  # sanity ping for the SQL layer used in dev
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB check failed: {e!s}")

@app.get("/version", tags=["Meta"])
def version():
    return {"name": APP_NAME, "version": APP_VERSION}
