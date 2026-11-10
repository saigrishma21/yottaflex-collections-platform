"""FastAPI Application Main Entry Point.

YottaFlex AI Collections & Delinquency Management Platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/", tags=["Health"])
def health_check():
    """System health check and overview."""
    return {
        "status": "ONLINE",
        "service": "YottaFlex AI Collections Platform",
        "version": "1.0.0",
        "documentation": "/docs",
        "features": [
            "Explainable Prioritization Scoring",
            "Statutory Contact Window Scheduling (FDCPA)",
            "Promise to Pay State Machine",
            "Automated Compliance Violation Detector",
            "Deterministic Fixed-Seed Synthetic Data (20261022)",
            "Ground Truth Evaluation Benchmark",
        ],
    }
