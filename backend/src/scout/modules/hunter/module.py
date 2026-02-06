"""
Hunter Mode Module.

Proactive vulnerability scanning module that searches
for weaknesses before attackers can exploit them.
"""

from datetime import datetime, timezone
from typing import Any

from scout.core.logging import get_logger
from scout.modules.base import (
    BaseModule,
    ExecutionContext,
    ModuleMode,
    ModuleResult,
)

logger = get_logger(__name__)


class HunterModule(BaseModule):
    """
    Hunter Mode - Proactive Vulnerability Scanner.

    This module:
    - Scans internal network for open ports
    - Checks for known vulnerabilities
    - Tests for weak configurations
    - Reports findings for remediation

    Key principle: Find vulnerabilities before attackers do.
    """

    name = "hunter"
    description = "Proactive vulnerability scanning and discovery"
    version = "0.1.0"
    supported_modes = [ModuleMode.ACTIVE, ModuleMode.SIMULATION]

    def __init__(self) -> None:
        super().__init__()
        self._scan_results: list[dict[str, Any]] = []

    async def execute(self, context: ExecutionContext) -> ModuleResult:
        """
        Execute hunter mode scanning.

        In a real implementation, this would:
        1. Discover hosts on the network
        2. Scan for open ports
        3. Identify running services
        4. Check for known vulnerabilities
        """
        start_time = datetime.now(timezone.utc)
        self._logger.info("hunter_mode_started", mode=context.mode)

        # Get target from config or default to local network
        target = context.config.get("target", "localhost")

        # Perform scan
        try:
            findings = await self.scan_host(context=context, target_ip=target)
        except Exception as e:
            self._logger.error("scan_failed", error=str(e))
            findings = {"error": str(e)}

        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        completed_at = datetime.now(timezone.utc)

        # Persist to ScanResult for history
        if context.scan_result_repo and context.user_id and "error" not in findings:
            try:
                await context.scan_result_repo.create(
                    user_id=context.user_id,
                    scan_type="nmap",
                    scanner_used="nmap",
                    target=target,
                    status="completed",
                    open_ports=findings.get("open_ports") or [],
                    services_found=findings.get("services") or [],
                    parsed_results=findings.get("raw_data") or {},
                    started_at=start_time,
                    completed_at=completed_at,
                    duration_seconds=int(execution_time / 1000),
                )
            except Exception as e:
                self._logger.error("failed_to_persist_scan_result", error=str(e))

        return ModuleResult(
            success=True,
            message=f"Hunt completed on {target}",
            data=findings,
            execution_time_ms=execution_time,
        )

    async def _perform_scan(self, context: ExecutionContext) -> dict[str, Any]:
        """
        Internal method to perform network scan.

        This is a stub that will be replaced with actual implementation.
        """
        # Stub implementation
        return {
            "hosts_scanned": 0,
            "open_ports": [],
            "vulnerabilities": [],
            "recommendations": [],
        }

    async def scan_host(
        self,
        target_ip: str,
        context: ExecutionContext | None = None,
        port_range: tuple[int, int] = (1, 1024),
    ) -> dict[str, Any]:
        """
        Scan a specific host for open ports.

        Args:
            target_ip: IP address to scan
            context: Execution context (for asset_repo when persisting)
            port_range: Tuple of (start_port, end_port)

        Returns:
            Scan results including open ports and services
        """
        self._logger.info(
            "scanning_host",
            target=target_ip,
            port_range=f"{port_range[0]}-{port_range[1]}",
        )

        from scout.tools.registry import tool_registry
        nmap_tool = tool_registry.get_tool("nmap_scanner")
        
        if not nmap_tool:
            self._logger.error("nmap_tool_not_found")
            return {"error": "Nmap tool not available"}

        # Run Nmap
        result = await nmap_tool.run(hosts=target_ip, arguments="-sV -O -F --open -T4")
        
        if not result.success:
            self._logger.error("nmap_scan_failed", error=result.error)
            return {"error": result.error}

        ids = result.data.get("hosts", {})
        scan_data = ids.get(target_ip, {})
        
        open_ports = []
        services = []
        
        # Parse ports
        if "tcp" in scan_data:
            for port, info in scan_data["tcp"].items():
                open_ports.append(port)
                service_name = info.get("name", "unknown")
                product = info.get("product", "")
                version = info.get("version", "")
                full_service = f"{service_name} {product} {version}".strip()
                services.append(full_service)
        
        # PERSIST TO DATABASE
        if context is not None and context.asset_repo:
            try:
                from uuid import UUID
                # TODO: Get actual user ID from context once auth is fully passed
                DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
                
                # Check if asset exists
                existing_asset = await context.asset_repo.get_by_ip(DEMO_USER_ID, target_ip)
                
                asset_data = {
                    "asset_type": "ip",
                    "value": target_ip,
                    "ip_address": target_ip,
                    "label": (scan_data.get("hostnames") or [{}])[0].get("name") or target_ip,
                    "open_ports": open_ports,
                    "description": f"Scanned by Hunter at {datetime.utcnow().isoformat()}. Services: {', '.join(services[:5])}...",
                    "status": "active" if open_ports else "online",
                    "vulnerability_count": 0,
                    "risk_score": 0.0,
                }

                if existing_asset:
                    self._logger.info("updating_asset", ip=target_ip)
                    # Update existing asset
                    # Note: AssetRepository.update expects kwargs
                    await context.asset_repo.update(
                        existing_asset.id,
                        open_ports=open_ports,
                        description=asset_data["description"]
                    )
                else:
                    self._logger.info("creating_new_asset", ip=target_ip)
                    await context.asset_repo.create(
                        user_id=DEMO_USER_ID,
                        **asset_data
                    )
            except Exception as e:
                self._logger.error("failed_to_persist_asset", error=str(e))

        return {
            "target": target_ip,
            "open_ports": open_ports,
            "services": services,
            "raw_data": scan_data
        }
