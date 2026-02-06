from datetime import datetime
from pydantic import Field
from scout.domain.entities.base import Entity

class PacketLog(Entity):
    """
    Represents a captured network packet summary.
    Optimized for time-series storage.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_ip: str
    destination_ip: str
    protocol: str
    length: int
    info: str | None = None
    
    # Metadata
    interface: str
    direction: str = "unknown"  # inbound, outbound, internal
    
    def log_line(self) -> str:
        return f"[{self.timestamp}] {self.protocol} {self.source_ip} -> {self.destination_ip} ({self.length} bytes)"
