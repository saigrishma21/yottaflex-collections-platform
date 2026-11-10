"""FastAPI Application Main Entry Point.

YottaFlex AI Collections & Delinquency Management Platform.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.routes import (
    customers,
    loans,
    collections,
    compliance,
    dashboard,
)

app = FastAPI(
    title="YottaFlex AI Delinquency & Collections Platform",
    description=(
        "Prioritize overdue accounts, schedule contact tasks, and monitor commitments "
        "without aggressive or unlawful practices. Exposes explainable decision scoring, "
        "immutable audit traceability, and statutory compliance guardrails."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for React Frontend (Vite default port 5173 or other local ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard.router)
app.include_router(collections.router)
app.include_router(compliance.router)
app.include_router(customers.router)
app.include_router(loans.router)

# Mount bundled production React frontend if built
FRONTEND_DIST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "dist",
)
if os.path.exists(FRONTEND_DIST):
    ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    app.mount("/app", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


@app.get("/", tags=["Health"])
def health_check():
    """System health check and overview."""
    return {
        "status": "ONLINE",
        "service": "YottaFlex AI Collections Platform",
        "version": "1.0.0",
        "documentation": "/docs",
        "web_dashboard": "/app" if os.path.exists(FRONTEND_DIST) else "Run 'npm run dev' in /frontend",
        "features": [
            "Explainable Prioritization Scoring",
            "Statutory Contact Window Scheduling (FDCPA)",
            "Promise to Pay State Machine",
            "Automated Compliance Violation Detector",
            "Deterministic Fixed-Seed Synthetic Data (20261022)",
            "Ground Truth Evaluation Benchmark",
        ],
    }

