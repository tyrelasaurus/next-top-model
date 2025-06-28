"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events
    """
    # Startup
    logger.info("Starting up Sports Data Aggregator API...")
    yield
    # Shutdown
    logger.info("Shutting down Sports Data Aggregator API...")


# Create FastAPI instance
app = FastAPI(
    title="Sports Data Aggregator API",
    description="API for aggregating sports data from multiple sources",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to Sports Data Aggregator API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


# Import and include routers
from .api.v1 import teams, games, players, data_management
from .core.config import settings

app.include_router(teams.router, prefix=f"{settings.API_V1_STR}/teams", tags=["teams"])
app.include_router(games.router, prefix=f"{settings.API_V1_STR}/games", tags=["games"])
app.include_router(players.router, prefix=f"{settings.API_V1_STR}/players", tags=["players"])
app.include_router(data_management.router, prefix=f"{settings.API_V1_STR}/data", tags=["data-management"])