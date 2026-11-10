"""FastAPI Application Main Entry Point.

YottaFlex AI Collections & Delinquency Management Platform.
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
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
        app.mount("/app/assets", StaticFiles(directory=ASSETS_DIR), name="app_assets")

    INDEX_HTML = os.path.join(FRONTEND_DIST, "index.html")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    def serve_frontend_spa():
        """Serve SPA index.html with strict no-cache headers to prevent stale asset hashes."""
        return FileResponse(
            INDEX_HTML,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    # Mount remaining root static files (favicon, etc.)
    app.mount("/app", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


@app.get("/", tags=["Health"])
def health_check(request: Request = None):
    """System health check and overview. Auto-redirects browser requests to /app/."""
    if request:
        accept = request.headers.get("accept", "")
        if "text/html" in accept and os.path.exists(FRONTEND_DIST):
            return RedirectResponse(url="/app/")
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

