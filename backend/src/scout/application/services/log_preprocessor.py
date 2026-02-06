"""
Log Preprocessor - Öncelik tabanlı filtreleme ve kota.

Binlerce log satırında kritik satırları koruyup LLM'e gidecek içeriği ve meta bilgisini üretir.
Hibrit modda daha sıkı limit uygulanır.
"""

from dataclasses import dataclass
from typing import List

from scout.core.config import get_settings
from scout.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PreprocessedLogs:
    """Ön işlenmiş log çıktısı."""
    content: str
    total_lines: int
    lines_analyzed: int
    priority_lines_included: int
    rest_lines_dropped: int
    was_truncated: bool
    hybrid_mode_used: bool


def _is_priority_line(line: str, keywords: List[str], severity_patterns: List[str]) -> bool:
    """Satır öncelikli mi (severity veya anahtar kelime)."""
    line_upper = line.upper()
    line_lower = line.lower()
    for pat in severity_patterns:
        if pat.upper() in line_upper:
            return True
    for kw in keywords:
        if kw.lower() in line_lower:
            return True
    return False


def preprocess(logs: str, query: str, hybrid: bool = False) -> PreprocessedLogs:
    """
    Log metnini öncelik + kota ile işler; LLM'e gidecek content ve meta döner.

    Args:
        logs: Ham log metni.
        query: Kullanıcı sorusu (ileride query'den kelime çıkarımı için kullanılabilir).
        hybrid: True ise hibrit mod limitleri uygulanır.

    Returns:
        PreprocessedLogs: content (LLM'e verilecek metin), meta alanları.
    """
    settings = get_settings()
    keywords = list(settings.log_priority_keywords)
    severity_patterns = list(settings.log_priority_severity_patterns)

    if hybrid:
        max_lines = settings.log_hybrid_max_lines
        max_chars = settings.log_hybrid_max_chars
    else:
        max_lines = settings.log_max_lines
        max_chars = settings.log_max_chars

    lines = [ln.strip() for ln in logs.strip().splitlines() if ln.strip()]
    total_lines = len(lines)

    priority_lines: List[str] = []
    rest_lines: List[str] = []
    for ln in lines:
        if _is_priority_line(ln, keywords, severity_patterns):
            priority_lines.append(ln)
        else:
            rest_lines.append(ln)

    selected: List[str] = []
    selected.extend(priority_lines)
    priority_count = len(priority_lines)
    remaining_slots = max_lines - priority_count
    rest_dropped = 0

    if remaining_slots > 0 and rest_lines:
        if len(rest_lines) <= remaining_slots:
            selected.extend(rest_lines)
        else:
            step = max(1, len(rest_lines) // remaining_slots)
            sampled = [rest_lines[i] for i in range(0, len(rest_lines), step)][:remaining_slots]
            selected.extend(sampled)
            rest_dropped = len(rest_lines) - len(sampled)
    elif rest_lines:
        rest_dropped = len(rest_lines)

    content = "\n".join(selected)
    if len(content) > max_chars:
        content = content[:max_chars].rsplit("\n", 1)[0]
    lines_analyzed = len(content.splitlines())
    was_truncated = total_lines > lines_analyzed or rest_dropped > 0

    logger.info(
        "log_preprocessed",
        total_lines=total_lines,
        lines_analyzed=lines_analyzed,
        priority_included=priority_count,
        rest_dropped=rest_dropped,
        hybrid=hybrid,
    )

    return PreprocessedLogs(
        content=content,
        total_lines=total_lines,
        lines_analyzed=lines_analyzed,
        priority_lines_included=priority_count,
        rest_lines_dropped=rest_dropped,
        was_truncated=was_truncated,
        hybrid_mode_used=hybrid,
    )
