"""
Defense Mode Module.

Active protection module that can take defensive actions
such as blocking IPs, resetting connections, etc.

Supports Human-in-the-Loop (HITL) approval workflow for destructive actions.
"""

from datetime import datetime
from typing import Any, Union

from scout.core.logging import get_logger
from scout.domain.events import ActionExecutedEvent
from scout.domain.entities.pending_action import ActionSeverity
from scout.modules.base import (
    BaseModule,
    ExecutionContext,
    ModuleMode,
    ModuleResult,
)

logger = get_logger(__name__)


class DefenseModule(BaseModule):
    """
    Defense Mode - Active Protection.

    This module:
    - Monitors for active threats
    - Can block suspicious IPs via firewall
    - Can reset malicious connections
    - Integrates with IPS/IDS systems

    Key principle: Minimize false positives before taking action.
    """

    name = "defense"
    description = "Active threat protection and response"
    version = "0.1.0"
    supported_modes = [ModuleMode.ACTIVE, ModuleMode.SIMULATION]

    def __init__(self) -> None:
        super().__init__()
        self._blocked_ips: set[str] = set()
        self._actions_taken: list[dict[str, Any]] = []

    async def execute(self, context: ExecutionContext) -> ModuleResult:
        """
        Execute defense mode protection.

        In a real implementation, this would:
        1. Monitor threat repository for confirmed threats
        2. Take appropriate actions based on threat type
        3. Log all actions taken
        """
        start_time = datetime.utcnow()
        self._logger.info("defense_mode_started", mode=context.mode)

        actions = []

        # TODO: Implement actual defense logic
        # For now, return a stub result

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ModuleResult(
            success=True,
            message="Defense scan completed",
            data={
                "blocked_ips": list(self._blocked_ips),
                "actions_taken": actions,
                "mode": context.mode.value,
            },
            execution_time_ms=execution_time,
        )

    async def block_ip(
        self,
        ip: str,
        reason: str,
        context: ExecutionContext,
        severity: ActionSeverity = ActionSeverity.HIGH,
        confidence_score: float = 0.8,
    ) -> Union[bool, Any]:
        """
        Block an IP address.

        If HITL approval is required (based on context.require_approval),
        this will create a pending action and return it.
        Otherwise, it executes immediately.

        Args:
            ip: IP address to block
            reason: Reason for blocking
            context: Execution context with dependencies
            severity: Severity level (affects timeout)
            confidence_score: AI confidence (0.0-1.0)

        Returns:
            bool: True if executed immediately
            PendingAction: If approval is required (caller should wait)
        """
        self._logger.info("blocking_ip", ip=ip, reason=reason, mode=context.mode)

        # ─────────────────────────────────────────────────────────────────────
        # HITL Check: Request approval if required
        # ─────────────────────────────────────────────────────────────────────
        if (
            context.require_approval
            and context.approval_service
            and context.user_id
            and context.mode == ModuleMode.ACTIVE
        ):
            pending_action = await context.approval_service.request_approval(
                user_id=context.user_id,
                action_type="block_ip",
                module_name=self.name,
                target=ip,
                target_type="ip",
                reason=reason,
                severity=severity,
                action_params={"ip": ip, "reason": reason},
                confidence_score=confidence_score,
            )

            if pending_action:
                # Approval required - return the pending action
                self._logger.info(
                    "approval_requested",
                    action_type="block_ip",
                    target=ip,
                    pending_action_id=str(pending_action.id),
                )
                return pending_action

        # ─────────────────────────────────────────────────────────────────────
        # No approval required or in simulation mode - execute immediately
        # ─────────────────────────────────────────────────────────────────────
        return await self.block_ip_direct(ip, reason, context)

    async def block_ip_direct(
        self, ip: str, reason: str, context: ExecutionContext
    ) -> bool:
        """
        Block an IP address directly (bypasses HITL).

        Called either:
        - After approval is granted
        - When HITL is disabled
        - In simulation mode
        """
        if context.mode == ModuleMode.SIMULATION:
            self._logger.info("simulation_block", ip=ip)
            action = {"type": "block_ip", "target": ip, "simulated": True}
        else:
            # TODO: Implement actual IP blocking (iptables, Windows Firewall, etc.)
            self._blocked_ips.add(ip)
            action = {"type": "block_ip", "target": ip, "simulated": False}

        self._actions_taken.append(action)
        self.last_action_time = datetime.utcnow()
        self.tasks_completed += 1

        # Publish event
        if context.event_publisher:
            event = ActionExecutedEvent(
                action_type="block_ip",
                target=ip,
                success=True,
                details=reason,
            )
            await context.event_publisher.publish(event)

        self._logger.info(
            "ip_blocked",
            ip=ip,
            reason=reason,
            mode=context.mode.value,
        )

        return True

    async def unblock_ip(
        self,
        ip: str,
        context: ExecutionContext | None = None,
        require_approval: bool = False,
    ) -> Union[bool, Any]:
        """
        Unblock a previously blocked IP.

        Args:
            ip: IP address to unblock
            context: Optional execution context for HITL
            require_approval: Whether to require approval

        Returns:
            bool: True if executed, False if IP wasn't blocked
            PendingAction: If approval is required
        """
        # HITL check for unblock (usually less strict than block)
        if (
            require_approval
            and context
            and context.approval_service
            and context.user_id
        ):
            pending_action = await context.approval_service.request_approval(
                user_id=context.user_id,
                action_type="unblock_ip",
                module_name=self.name,
                target=ip,
                target_type="ip",
                reason="Requested IP unblock",
                severity=ActionSeverity.LOW,
                action_params={"ip": ip},
                confidence_score=0.95,
            )

            if pending_action:
                return pending_action

        # Execute directly
        return await self.unblock_ip_direct(ip)

    async def unblock_ip_direct(self, ip: str) -> bool:
        """Unblock an IP directly (bypasses HITL)."""
        if ip in self._blocked_ips:
            self._blocked_ips.remove(ip)
            self._logger.info("ip_unblocked", ip=ip)
            self.last_action_time = datetime.utcnow()
            return True
        return False

    def get_blocked_ips(self) -> list[str]:
        """Get list of currently blocked IPs."""
        return list(self._blocked_ips)
