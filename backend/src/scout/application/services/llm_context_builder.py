"""
LLM Context Builder.

Builds a text summary of recent traffic, scan results, and assets for use in LLM prompts
(chat, agent, or analysis endpoints).
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.repositories import (
    AssetRepository,
    ScanResultRepository,
    TrafficRepository,
)


async def build_llm_context(
    session: AsyncSession,
    user_id: UUID,
    *,
    traffic_since_minutes: int = 60,
    traffic_interval_minutes: int = 15,
    scan_results_limit: int = 10,
    assets_limit: int = 50,
    max_context_chars: int = 8000,
) -> str:
    """
    Build a single text block summarizing recent traffic, scan results, and assets
    for injection into an LLM system or user prompt.

    Returns a string with sections: Son trafik, Son taramalar, Asset'ler.
    """
    traffic_repo = TrafficRepository(session)
    scan_repo = ScanResultRepository(session)
    asset_repo = AssetRepository(session)

    parts: list[str] = []

    # Traffic summary
    try:
        agg = await traffic_repo.get_aggregates(
            since_minutes=traffic_since_minutes,
            interval_minutes=traffic_interval_minutes,
        )
        ts = agg.get("time_series") or []
        total_packets = sum(b.get("packet_count", 0) for b in ts)
        total_bytes = sum(b.get("byte_count", 0) for b in ts)
        parts.append(
            "## Son trafik\n"
            f"Son {traffic_since_minutes} dakikada toplam {total_packets} paket, {total_bytes} byte. "
            f"Aralık: {traffic_interval_minutes} dk."
        )
        if ts:
            recent = ts[-5:] if len(ts) >= 5 else ts
            parts.append(
                " Son dönemler: " + ", ".join(f"{b.get('bucket_start', '')}: {b.get('packet_count', 0)} pk" for b in recent)
            )
        parts.append("\n")
    except Exception:
        parts.append("## Son trafik\nVeri alınamadı.\n")

    # Scan results summary
    try:
        scans = await scan_repo.list_by_user(user_id, limit=scan_results_limit)
        parts.append("## Son taramalar\n")
        if not scans:
            parts.append("Tarama kaydı yok.\n")
        else:
            for s in scans[:scan_results_limit]:
                target = getattr(s, "target", "?")
                status = getattr(s, "status", "?")
                open_ports = getattr(s, "open_ports", None) or []
                ports_str = ", ".join(str(p) for p in open_ports[:10]) if open_ports else "yok"
                if len(open_ports) > 10:
                    ports_str += f" (+{len(open_ports) - 10})"
                parts.append(f"- {target} | {status} | açık portlar: {ports_str}\n")
        parts.append("\n")
    except Exception:
        parts.append("## Son taramalar\nVeri alınamadı.\n")

    # Assets summary
    try:
        assets = await asset_repo.get_by_user(user_id, limit=assets_limit)
        parts.append("## Asset'ler\n")
        if not assets:
            parts.append("Asset kaydı yok.\n")
        else:
            parts.append(f"Toplam {len(assets)} asset. Örnekler:\n")
            for a in assets[:15]:
                ip = getattr(a, "ip_address", None) or getattr(a, "value", "?")
                label = getattr(a, "label", None) or ip
                ports = getattr(a, "open_ports", None) or []
                parts.append(f"- {label} ({ip}) | portlar: {ports[:8]}\n")
        parts.append("\n")
    except Exception:
        parts.append("## Asset'ler\nVeri alınamadı.\n")

    text = "".join(parts)
    if len(text) > max_context_chars:
        text = text[: max_context_chars - 50] + "\n... (kısaltıldı)"
    return text.strip()
