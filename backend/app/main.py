"""FastAPI application entry point for the Unilog Enrichment Platform."""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path)
# Also try the backend-local .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .api import enrichment, jobs, export, status

app = FastAPI(
    title="Unilog Product Enrichment Intelligence",
    description="Manufacturer Source Discovery & URL Intelligence API",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(status.router, prefix="/api", tags=["Status"])
app.include_router(enrichment.router, prefix="/api", tags=["Enrichment"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(export.router, prefix="/api", tags=["Export"])


@app.get("/")
def root():
    return {
        "name": "Unilog Product Enrichment Intelligence",
        "version": "1.0.0",
        "docs": "/docs",
    }
