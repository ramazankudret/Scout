"""
Lesson Export Service - learned_lessons verisini eğitim formatında (JSONL) dışa aktarır.

Lesson Model pipeline'ının ilk adımı: veri hazır olduğunda LoRA eğitimi için
kullanılacak dosyayı üretir.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scout.core.config import get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
from scout.core.logger import get_logger
from scout.infrastructure.database.models import LearnedLesson

logger = get_logger(__name__)


def _lesson_to_training_record(lesson: LearnedLesson) -> dict[str, Any]:
    """
    Tek bir LearnedLesson kaydını eğitim için instruction/output formatına çevirir.
    Mevcut ORM kolonları kullanılır (failure_type, root_cause, proposed_solution vb.).
    """
    parts: list[str] = []
    if lesson.failure_type:
        parts.append(f"Failure type: {lesson.failure_type}")
    if lesson.failure_description:
        parts.append(f"Description: {lesson.failure_description}")
    if lesson.what_happened:
        parts.append(f"What happened: {lesson.what_happened}")
    if lesson.why_it_happened:
        parts.append(f"Why: {lesson.why_it_happened}")
    if lesson.what_was_expected:
        parts.append(f"Expected: {lesson.what_was_expected}")
    if lesson.gap_analysis:
        parts.append(f"Gap: {lesson.gap_analysis}")
    instruction = " | ".join(parts) if parts else "Security lesson (no context)"

    out_parts: list[str] = []
    if lesson.root_cause:
        out_parts.append(f"Root cause: {lesson.root_cause}")
    if lesson.proposed_solution:
        out_parts.append(f"Solution: {lesson.proposed_solution}")
    if lesson.solution_type:
        out_parts.append(f"Type: {lesson.solution_type}")
    if lesson.implementation_steps and isinstance(lesson.implementation_steps, list):
        out_parts.append(f"Steps: {', '.join(str(s) for s in lesson.implementation_steps)}")
    if lesson.priority:
        out_parts.append(f"Priority: {lesson.priority}")
    output = " | ".join(out_parts) if out_parts else "No structured output"

    return {
        "instruction": instruction,
        "output": output,
    }


async def export_lessons_to_jsonl(
    session: "AsyncSession",  # noqa: F821
    output_path: Path | None = None,
    batch_size: int = 500,
) -> tuple[Path, int]:
    """
    Tüm learned_lessons kayıtlarını JSONL dosyasına yazar.

    Args:
        session: AsyncSession (get_db_context ile alınır).
        output_path: Yazılacak dosya. None ise config.lesson_export_dir içinde
                     lessons_latest.jsonl kullanılır.
        batch_size: Her batch'te kaç kayıt çekileceği.

    Returns:
        (yazılan dosya path'i, toplam kayıt sayısı)
    """
    from scout.infrastructure.repositories.learning_repository import LearningRepository

    settings = get_settings()
    if output_path is None:
        export_dir = Path(settings.lesson_export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / "lessons_latest.jsonl"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    repo = LearningRepository(session)
    total = await repo.count()
    written = 0

    with open(output_path, "w", encoding="utf-8") as f:
        for skip in range(0, total, batch_size):
            lessons = await repo.get_all(skip=skip, limit=batch_size)
            for lesson in lessons:
                record = _lesson_to_training_record(lesson)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1

    logger.info("lesson_export_complete", path=str(output_path), count=written)
    return output_path, written
