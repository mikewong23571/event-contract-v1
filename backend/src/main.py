"""
Event Contract Trading System - Backend API

FastAPI application entry point for the trading system backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.signals import router as signals_router
from .api.market_data import router as market_data_router
from .api.risk import router as risk_router

# Initialize FastAPI application
app = FastAPI(
    title="Event Contract Trading System API",
    description="API for probability-based trading signals and risk management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Event Contract Trading System API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "backend"}

# Include API routers
app.include_router(signals_router, prefix="/api/v1")
app.include_router(market_data_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
