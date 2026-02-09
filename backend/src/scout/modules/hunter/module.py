"""
Hunter Mode Module.

Proactive vulnerability scanning module that searches
for weaknesses before attackers can exploit them.
"""

import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from scout.core.logging import get_logger
from scout.modules.base import (
    BaseModule,
    ExecutionContext,
    ModuleMode,
    ModuleResult,
)

logger = get_logger(__name__)

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _is_cidr(target: str) -> bool:
    """Return True if target looks like a CIDR range (e.g. 192.168.1.0/24)."""
    if not target or "/" not in target:
        return False
    return bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$", target.strip()))


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

        - If target is a CIDR (e.g. 192.168.1.0/24): run discovery (Nmap -sn or Netdiscover),
          create/update assets for each discovered IP; optionally skip per-host port scan.
        - If target is a single IP: run existing scan_host (port scan + persist asset).
        """
        start_time = datetime.now(timezone.utc)
        self._logger.info("hunter_mode_started", mode=context.mode)

        target = context.config.get("target", "localhost")
        if isinstance(target, str):
            target = target.strip()
        scan_discovered = context.config.get("scan_discovered") is True

        try:
            if _is_cidr(target) and scan_discovered:
                findings = await self._discover_and_scan_subnet(context=context, cidr=target)
            elif _is_cidr(target):
                findings = await self._discover_subnet(context=context, cidr=target)
            else:
                findings = await self.scan_host(context=context, target_ip=target)
        except Exception as e:
            self._logger.error("scan_failed", error=str(e))
            findings = {"error": str(e)}

        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        completed_at = datetime.now(timezone.utc)

        if context.scan_result_repo and context.user_id and "error" not in findings:
            raw_output: str | None = findings.get("process_output")
            if not raw_output and findings.get("steps"):
                parts = []
                for s in findings["steps"]:
                    parts.append(f"$ {s.get('command', '')}")
                    if s.get("output"):
                        parts.append(s["output"])
                raw_output = "\n".join(parts) if parts else None
            try:
                await context.scan_result_repo.create(
                    user_id=context.user_id,
                    scan_type="nmap" if not _is_cidr(target) else "discovery",
                    scanner_used="nmap" if not _is_cidr(target) else findings.get("scanner_used", "nmap"),
                    target=target,
                    status="completed",
                    open_ports=findings.get("open_ports") or [],
                    services_found=findings.get("services") or [],
                    parsed_results=findings.get("raw_data") or {},
                    started_at=start_time,
                    completed_at=completed_at,
                    duration_seconds=int(execution_time / 1000),
                    raw_output=raw_output,
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
        return {
            "hosts_scanned": 0,
            "open_ports": [],
            "vulnerabilities": [],
            "recommendations": [],
        }

    async def _discover_subnet(
        self,
        context: ExecutionContext,
        cidr: str,
    ) -> dict[str, Any]:
        """
        Discover hosts in a CIDR range via Nmap -sn or Netdiscover; create/update assets for each IP.
        """
        import asyncio
        from scout.tools.registry import tool_registry

        user_id = context.user_id or DEMO_USER_ID
        discovered_ips: list[str] = []
        netdiscover_hosts: list[dict[str, Any]] = []
        scanner_used = "nmap"
        steps: list[dict[str, Any]] = []

        # Prefer Nmap -sn -PR (host discovery + ARP for MAC)
        from scout.tools.oui_lookup import oui_to_vendor
        hosts_data: dict[str, Any] = {}
        nmap_tool = tool_registry.get_tool("nmap_scanner")
        if nmap_tool:
            try:
                result = await asyncio.wait_for(
                    nmap_tool.run(hosts=cidr, arguments="-sn -PR"),
                    timeout=300.0,
                )
                if result.success and result.data:
                    hosts_data = result.data.get("hosts") or {}
                    discovered_ips = [h for h in hosts_data.keys() if h and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", h)]
                    cmd = result.data.get("command") or f"nmap -sn -PR {cidr}"
                    out_lines = [f"Discovered {len(discovered_ips)} host(s):"] + (discovered_ips[:20] if discovered_ips else [])
                    if len(discovered_ips) > 20:
                        out_lines.append(f"... and {len(discovered_ips) - 20} more")
                    steps.append({"command": cmd, "output": "\n".join(out_lines), "status": "success"})
            except asyncio.TimeoutError:
                self._logger.warning("nmap_discovery_timeout", cidr=cidr)
            except Exception as e:
                self._logger.warning("nmap_discovery_failed", error=str(e))

        # Fallback to Netdiscover if Nmap found nothing or failed
        if not discovered_ips:
            netdiscover_tool = tool_registry.get_tool("netdiscover")
            if netdiscover_tool:
                try:
                    result = await asyncio.wait_for(
                        netdiscover_tool.run(ip_range=cidr),
                        timeout=120.0,
                    )
                    if result.success and result.data:
                        hosts = result.data.get("hosts") or []
                        netdiscover_hosts = [h for h in hosts if isinstance(h, dict) and h.get("ip")]
                        discovered_ips = [h.get("ip") for h in netdiscover_hosts]
                        scanner_used = "netdiscover"
                        cmd = f"netdiscover -r {cidr} -P -N"
                        out_lines = [f"Discovered {len(discovered_ips)} host(s):"] + (discovered_ips[:20] if discovered_ips else [])
                        if len(discovered_ips) > 20:
                            out_lines.append(f"... and {len(discovered_ips) - 20} more")
                        steps.append({"command": cmd, "output": "\n".join(out_lines), "status": "success"})
                except (asyncio.TimeoutError, Exception) as e:
                    self._logger.warning("netdiscover_failed", error=str(e))

        if not discovered_ips:
            return {
                "error": "No hosts discovered. If the backend runs in Docker (bridge network), it cannot reach your LAN (192.168.x). Stop the normal backend, then run: docker compose -f docker/docker-compose.scan.yml up -d backend",
                "cidr": cidr,
                "discovered_ips": [],
                "discovered_hosts": [],
                "count": 0,
                "steps": steps,
                "command": steps[0]["command"] if steps else None,
            }

        # Build discovered_hosts with MAC and vendor (from nmap hosts_data or netdiscover_hosts)
        discovered_hosts = []
        netdiscover_by_ip = {h["ip"]: h for h in netdiscover_hosts} if netdiscover_hosts else {}
        for ip in discovered_ips:
            mac = None
            vendor = "Unknown"
            if netdiscover_by_ip and ip in netdiscover_by_ip:
                mac = netdiscover_by_ip[ip].get("mac")
                vendor = (netdiscover_by_ip[ip].get("vendor") or "").strip() or oui_to_vendor(mac)
            elif hosts_data and ip in hosts_data:
                addrs = hosts_data[ip].get("addresses") or {}
                if isinstance(addrs, dict):
                    mac = addrs.get("mac")
                if isinstance(mac, list):
                    mac = mac[0] if mac else None
                vendor = oui_to_vendor(mac) if mac else "Unknown"
            discovered_hosts.append({"ip": ip, "mac": mac or "", "vendor": vendor})

        # Persist each discovered IP as asset (with MAC and vendor)
        if context.asset_repo:
            for entry in discovered_hosts:
                ip = entry["ip"]
                mac = entry.get("mac") or None
                vendor = entry.get("vendor") or "Unknown"
                try:
                    existing = await context.asset_repo.get_by_ip(user_id, ip)
                    if existing:
                        self._logger.debug("discovery_asset_exists", ip=ip)
                    else:
                        await context.asset_repo.create(
                            user_id=user_id,
                            asset_type="ip",
                            value=ip,
                            ip_address=ip,
                            label=ip,
                            open_ports=[],
                            description=f"Discovered by Hunter (subnet {cidr})",
                            status="online",
                            vulnerability_count=0,
                            risk_score=0.0,
                            mac_address=mac,
                            extra_data={"vendor": vendor},
                        )
                        self._logger.info("discovery_asset_created", ip=ip)
                except Exception as e:
                    self._logger.error("discovery_asset_create_failed", ip=ip, error=str(e))

        command = steps[0]["command"] if steps else f"{scanner_used} {cidr}"
        process_output = steps[0]["output"] if steps else f"Discovered {len(discovered_ips)} host(s): " + ", ".join(discovered_ips[:10])
        return {
            "cidr": cidr,
            "discovered_ips": discovered_ips,
            "discovered_hosts": discovered_hosts,
            "count": len(discovered_ips),
            "scanner_used": scanner_used,
            "raw_data": {"hosts": discovered_ips},
            "command": command,
            "process_output": process_output,
            "steps": steps,
        }

    async def _discover_and_scan_subnet(
        self,
        context: ExecutionContext,
        cidr: str,
        limit: int = 15,
    ) -> dict[str, Any]:
        """Discover hosts in CIDR then run port scan on each (up to limit). Returns scan_results list and merged steps."""
        discovery = await self._discover_subnet(context=context, cidr=cidr)
        if discovery.get("error"):
            return discovery
        discovered_ips = discovery.get("discovered_ips") or []
        if not discovered_ips:
            return discovery
        to_scan = discovered_ips[:limit]
        scan_results: list[dict[str, Any]] = []
        all_steps: list[dict[str, Any]] = list(discovery.get("steps") or [])
        for ip in to_scan:
            one = await self.scan_host(context=context, target_ip=ip)
            if one.get("error"):
                all_steps.append({"command": f"scan {ip}", "output": one["error"], "status": "error"})
                scan_results.append({"target": ip, "open_ports": [], "services": [], "error": one["error"]})
            else:
                for s in one.get("steps") or []:
                    all_steps.append(s)
                scan_results.append({
                    "target": one.get("target", ip),
                    "open_ports": one.get("open_ports") or [],
                    "services": one.get("services") or [],
                })
        return {
            "cidr": cidr,
            "discovered_ips": discovered_ips,
            "scan_results": scan_results,
            "steps": all_steps,
            "command": discovery.get("command"),
            "process_output": f"Discovered {len(discovered_ips)} host(s); scanned {len(to_scan)}.",
        }

    async def scan_host(
        self,
        target_ip: str,
        context: ExecutionContext | None = None,
        port_range: tuple[int, int] = (1, 1024),
        detailed: bool = False,
    ) -> dict[str, Any]:
        """
        Scan a specific host for open ports.

        Args:
            target_ip: IP address to scan
            context: Execution context (for asset_repo when persisting)
            port_range: Tuple of (start_port, end_port)
            detailed: If True, use -sV -O (service/version and OS detection), timeout 180s

        Returns:
            Scan results including open ports, services, and optionally os_family/os_name/os_version
        """
        if context and isinstance(context.config, dict):
            detailed = context.config.get("detailed", detailed)
        self._logger.info(
            "scanning_host",
            target=target_ip,
            detailed=detailed,
        )

        from scout.tools.registry import tool_registry
        nmap_tool = tool_registry.get_tool("nmap_scanner")
        
        if not nmap_tool:
            self._logger.error("nmap_tool_not_found")
            return {"error": "Nmap tool not available. Backend'de Nmap kurulu mu kontrol edin."}

        if detailed:
            nmap_args = "-sT -sV -O -F --open -T4"
            timeout_sec = 180.0
        else:
            nmap_args = "-sT -F --open -T4"
            timeout_sec = 90.0

        try:
            import asyncio
            result = await asyncio.wait_for(
                nmap_tool.run(hosts=target_ip, arguments=nmap_args),
                timeout=timeout_sec,
            )
        except asyncio.TimeoutError:
            self._logger.error("nmap_scan_timeout", target=target_ip)
            return {"error": f"Tarama {int(timeout_sec)} saniyede tamamlanamadı. Daha küçük hedef deneyin."}
        
        if not result.success:
            self._logger.error("nmap_scan_failed", error=result.error)
            return {"error": result.error}

        ids = result.data.get("hosts", {})
        scan_data = ids.get(target_ip, {}) or {}

        open_ports = []
        services = []
        tcp = scan_data.get("tcp") or {}
        for port, info in (tcp.items() if hasattr(tcp, "items") else []):
            pinfo = info if isinstance(info, dict) else {}
            open_ports.append(int(port))
            service_name = pinfo.get("name", "unknown")
            product = pinfo.get("product", "")
            version = pinfo.get("version", "")
            full_service = f"{service_name} {product} {version}".strip()
            services.append(full_service)

        os_family, os_name, os_version = None, None, None
        osmatch = scan_data.get("osmatch")
        if isinstance(osmatch, (list, tuple)) and len(osmatch) > 0:
            first = osmatch[0]
            name = first.get("name", "") if isinstance(first, dict) else ""
            if isinstance(name, str) and name:
                os_name = name
                parts = name.split(None, 1)
                if parts:
                    os_family = parts[0]
                    os_version = parts[1] if len(parts) > 1 else None

        command = (result.data or {}).get("command") or f"nmap {nmap_args} {target_ip}"
        process_lines = ["PORT\tSTATE\tSERVICE"]
        for port, info in (tcp.items() if hasattr(tcp, "items") else []):
            pinfo = info if isinstance(info, dict) else {}
            state = pinfo.get("state", "open")
            svc = pinfo.get("name", "unknown")
            process_lines.append(f"{port}/tcp\t{state}\t{svc}")
        process_output = "\n".join(process_lines) if len(process_lines) > 1 else "No open ports."
        steps = [
            {"command": command, "output": process_output, "status": "success"}
        ]

        asset_description = f"Scanned by Hunter at {datetime.utcnow().isoformat()}. Services: {', '.join(services[:5])}..."
        if os_name:
            asset_description += f" OS: {os_name}"

        if context is not None and context.asset_repo:
            try:
                user_id = context.user_id or DEMO_USER_ID
                existing_asset = await context.asset_repo.get_by_ip(user_id, target_ip)
                hostnames = scan_data.get("hostnames") or []
                label = target_ip
                if isinstance(hostnames, (list, tuple)) and hostnames and isinstance(hostnames[0], dict):
                    label = hostnames[0].get("name", target_ip) or target_ip
                asset_data: dict[str, Any] = {
                    "asset_type": "ip",
                    "value": target_ip,
                    "ip_address": target_ip,
                    "label": label,
                    "open_ports": open_ports,
                    "description": asset_description,
                    "status": "active" if open_ports else "online",
                    "vulnerability_count": 0,
                    "risk_score": 0.0,
                }
                if os_family is not None:
                    asset_data["os_family"] = os_family
                if os_name is not None:
                    asset_data["os_name"] = os_name
                if os_version is not None:
                    asset_data["os_version"] = os_version

                if existing_asset:
                    self._logger.info("updating_asset", ip=target_ip)
                    update_kw: dict[str, Any] = {
                        "open_ports": open_ports,
                        "description": asset_data["description"],
                    }
                    if os_family is not None:
                        update_kw["os_family"] = os_family
                    if os_name is not None:
                        update_kw["os_name"] = os_name
                    if os_version is not None:
                        update_kw["os_version"] = os_version
                    await context.asset_repo.update(existing_asset.id, **update_kw)
                else:
                    self._logger.info("creating_new_asset", ip=target_ip)
                    await context.asset_repo.create(user_id=user_id, **asset_data)
            except Exception as e:
                self._logger.error("failed_to_persist_asset", error=str(e))

        out: dict[str, Any] = {
            "target": target_ip,
            "open_ports": open_ports,
            "services": services,
            "raw_data": scan_data,
            "command": command,
            "process_output": process_output,
            "steps": steps,
        }
        if os_family is not None:
            out["os_family"] = os_family
        if os_name is not None:
            out["os_name"] = os_name
        if os_version is not None:
            out["os_version"] = os_version
        return out
