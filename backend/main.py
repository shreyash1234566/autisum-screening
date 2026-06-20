"""
main.py — FastAPI backend for AutiScreen
Run: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from routers import children, sessions, doctor, ml_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(
    title="AutiScreen API",
    description="India-focused autism screening — server-side analysis pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(children.router)
app.include_router(sessions.router)
app.include_router(doctor.router)
app.include_router(ml_router.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "AutiScreen API v1.0"}

@app.get("/")
def root():
    return {
        "message": "AutiScreen API",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
