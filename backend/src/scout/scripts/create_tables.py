"""
Database Initialization Script.

Creates all tables defined in SQLAlchemy models.
Enables 'vector' extension for pgvector support.

Usage:
    python -m scout.scripts.create_tables
"""

import asyncio
import logging
import sys
from sqlalchemy import text

# Add src to path if running directly
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from scout.infrastructure.database.session import engine
from scout.infrastructure.database.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create database tables."""
    try:
        async with engine.begin() as conn:
            logger.info("Enabling 'vector' extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            logger.info("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
