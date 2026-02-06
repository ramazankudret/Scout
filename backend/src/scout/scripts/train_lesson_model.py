"""
Lesson Model Training Pipeline - iskelet.

Veri yeterli olduğunda LoRA/QLoRA ile lesson model eğitimi tetiklenir.
Şu an: export çalıştırılır, min samples kontrol edilir; eğitim adımı placeholder.

Kullanım:
    poetry run python -m scout.scripts.train_lesson_model
"""

import asyncio
import logging
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    _src = Path(__file__).resolve().parents[2]
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from scout.application.services.lesson_export_service import export_lessons_to_jsonl
from scout.core.config import get_settings
from scout.infrastructure.database.session import get_db_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _count_jsonl_lines(path: Path) -> int:
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


async def run_export(settings) -> Path | None:
    """Export lessons to JSONL; return path or None on failure."""
    export_dir = Path(settings.lesson_export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_dir / "lessons_latest.jsonl"

    async with get_db_context() as session:
        path, count = await export_lessons_to_jsonl(session, output_path=output_path)
    return path


def run_training_placeholder(settings, jsonl_path: Path, count: int) -> None:
    """
    Eğitim adımı: şu an sadece log.
    İleride burada LoRA/QLoRA (HF PEFT veya Unsloth) çağrılacak.
    """
    logger.info(
        "training_step_skipped",
        reason="Manual training not implemented in this skeleton",
        jsonl_path=str(jsonl_path),
        samples=count,
        base_model=settings.lesson_model_base,
        output_dir=settings.lesson_model_output_dir,
    )
    # İleride: subprocess veya transformers/peft API ile eğitim
    # Ör: ollama_lesson_model için adapter üret, lesson_model_output_dir'e yaz


async def main() -> None:
    settings = get_settings()
    min_samples = settings.lesson_min_samples_for_training

    # 1. Export
    logger.info("Running lesson export...")
    jsonl_path = await run_export(settings)
    if not jsonl_path or not jsonl_path.exists():
        logger.warning("Export produced no file; aborting.")
        return

    count = _count_jsonl_lines(jsonl_path)
    logger.info("Export finished: %d records in %s", count, jsonl_path)

    # 2. Min samples kontrolü
    if count < min_samples:
        logger.warning(
            "Not enough samples for training: %d < %d. Training skipped.",
            count,
            min_samples,
        )
        return

    # 3. Eğitim (placeholder)
    run_training_placeholder(settings, jsonl_path, count)


if __name__ == "__main__":
    asyncio.run(main())
