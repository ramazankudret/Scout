"""
Scout Logger - Merkezi loglama sistemi
Structlog ile zengin, yapılandırılmış loglar
"""

import structlog
import logging
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup structlog for the entire application.
    Call this once at application startup.
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Add file logging if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(file_handler)

    # Development vs Production rendering
    processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a named logger instance.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id=123)
    """
    return structlog.get_logger(name)


# Pre-configured loggers for common modules
class LoggerFactory:
    """Factory for creating module-specific loggers"""
    
    @staticmethod
    def agent_logger(agent_name: str) -> structlog.stdlib.BoundLogger:
        return get_logger(f"scout.agent.{agent_name}")
    
    @staticmethod
    def api_logger() -> structlog.stdlib.BoundLogger:
        return get_logger("scout.api")
    
    @staticmethod
    def security_logger() -> structlog.stdlib.BoundLogger:
        return get_logger("scout.security")
    
    @staticmethod
    def llm_logger() -> structlog.stdlib.BoundLogger:
        return get_logger("scout.llm")
