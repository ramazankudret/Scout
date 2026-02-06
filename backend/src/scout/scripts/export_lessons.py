"""
Lesson Export Script - learned_lessons tablosunu JSONL eğitim formatında dışa aktarır.

Lesson Model pipeline'ının ilk adımı. Kullanım:
    poetry run python -m scout.scripts.export_lessons
    # veya
    cd backend && poetry run python -m scout.scripts.export_lessons
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure package root on path when run as script
if __name__ == "__main__" and __package__ is None:
    _src = Path(__file__).resolve().parents[2]
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from scout.application.services.lesson_export_service import export_lessons_to_jsonl
from scout.infrastructure.database.session import get_db_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    async with get_db_context() as session:
        path, count = await export_lessons_to_jsonl(session)
    logger.info("Export finished: %s (%d records)", path, count)


if __name__ == "__main__":
    asyncio.run(main())
