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

# Columns that may be missing on learned_lessons if table was created with an older schema.
# Each tuple: (column_name, sql_type_with_default).
LEARNED_LESSONS_ADD_COLUMNS = [
    ("agent_name", "VARCHAR(50)"),
    ("action_type", "VARCHAR(100)"),
    ("target", "VARCHAR(500)"),
    ("prevention_strategy", "TEXT"),
    ("category", "VARCHAR(50)"),
    ("severity", "VARCHAR(20)"),
    ("recommended_checks", "JSONB DEFAULT '[]'"),
    ("occurrence_count", "INTEGER DEFAULT 1"),
    ("effectiveness_rate", "NUMERIC(5,2)"),
    ("confidence_score", "NUMERIC(3,2) DEFAULT 0.5"),
    ("human_feedback_score", "INTEGER"),
    ("context_hash", "VARCHAR(64)"),
    ("related_incident_ids", "UUID[]"),
    ("verified", "BOOLEAN DEFAULT FALSE"),
    ("verified_by", "UUID REFERENCES users(id)"),
    ("verified_at", "TIMESTAMP WITH TIME ZONE"),
    ("verification_notes", "TEXT"),
    ("priority", "VARCHAR(20) DEFAULT 'medium'"),
    ("tags", "TEXT[]"),
]


async def migrate_learned_lessons_columns(conn):
    """Add missing columns to learned_lessons (idempotent). PostgreSQL ADD COLUMN IF NOT EXISTS."""
    for col_name, col_def in LEARNED_LESSONS_ADD_COLUMNS:
        try:
            await conn.execute(
                text(
                    f"ALTER TABLE learned_lessons "
                    f"ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                )
            )
        except Exception as e:
            logger.debug("Column %s: %s", col_name, e)
    try:
        await conn.execute(
            text(
                "ALTER TABLE learned_lessons "
                "ADD COLUMN IF NOT EXISTS vector_embedding vector(1536)"
            )
        )
    except Exception as e:
        logger.debug("vector_embedding: %s", e)


async def create_tables():
    """Create database tables."""
    try:
        async with engine.begin() as conn:
            logger.info("Enabling 'vector' extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            logger.info("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Migrating learned_lessons columns if needed...")
            await migrate_learned_lessons_columns(conn)
            
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
