"""Utility modules for the application."""
from . import KoiosClient
from .routes import ai_router

# Singleton instance for easy import
ai_client = KoiosClient()

__all__ = [
    "ai_client",
    "ai_router"
]
