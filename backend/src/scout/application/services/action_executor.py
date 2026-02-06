"""
Action Executor.

Executes approved defensive actions by delegating to appropriate modules.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from scout.core.logging import get_logger
from scout.infrastructure.database.models_approval import PendingAction

logger = get_logger(__name__)


class ActionExecutor:
    """
    Executes approved actions by delegating to appropriate modules.

    This service is responsible for:
    1. Looking up the correct module
    2. Building execution context
    3. Executing the action
    4. Recording results
    """

    def __init__(
        self,
        pending_action_repo: Any,  # PendingActionRepository
        module_registry: Any | None = None,  # ModuleRegistry
        event_publisher: Any | None = None,
    ):
        self.pending_action_repo = pending_action_repo
        self.module_registry = module_registry
        self.event_publisher = event_publisher

    async def execute(self, action: PendingAction) -> dict[str, Any]:
        """
        Execute an approved action.

        Args:
            action: The PendingAction to execute

        Returns:
            Execution result dictionary

        Raises:
            ValueError: If module not found or action type unknown
            Exception: If execution fails
        """
        # Mark as executing
        action.status = "executing"
        action.executed_at = datetime.utcnow()
        await self.pending_action_repo.update(action)

        # Pre-execution: check learned lessons and recommended checks (strategy update from Feedback Loop)
        try:
            from scout.agents.learning_engine import learning_engine
            checks = learning_engine.get_prevention_checks(action.action_type)
            advice = await learning_engine.get_lesson_advice(
                action_type=action.action_type,
                target=action.target,
                context={"module": action.module_name},
            )
            if checks or advice:
                logger.info(
                    "action_pre_checks",
                    action_type=action.action_type,
                    target=action.target,
                    recommended_checks=checks,
                    lesson_advice_preview=advice[:200] if advice else None,
                )
        except Exception as e:
            logger.debug("learning_engine_pre_check_skipped", action_type=action.action_type, error=str(e))

        try:
            # Execute action based on type
            result = await self._execute_action(
                action_type=action.action_type,
                module_name=action.module_name,
                target=action.target,
                params=action.action_params,
            )

            # Mark as completed
            action.status = "completed"
            action.execution_result = result
            await self.pending_action_repo.update(action)

            logger.info(
                "action_executed",
                pending_action_id=str(action.id),
                action_type=action.action_type,
                target=action.target,
                result=result,
            )

            return result

        except Exception as e:
            # Mark as failed
            action.status = "failed"
            action.error_message = str(e)
            await self.pending_action_repo.update(action)

            logger.exception(
                "action_execution_failed",
                pending_action_id=str(action.id),
                action_type=action.action_type,
                error=str(e),
            )
            raise

    async def _execute_action(
        self,
        action_type: str,
        module_name: str,
        target: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute specific action type via module.

        This method dispatches to the appropriate module method.
        """
        # If no module registry, we can't execute
        if not self.module_registry:
            logger.warning(
                "no_module_registry",
                action_type=action_type,
                module_name=module_name,
            )
            return {
                "success": False,
                "error": "Module registry not configured",
                "action": action_type,
                "target": target,
            }

        # Get the module
        module = self.module_registry.get(module_name)
        if not module:
            raise ValueError(f"Module '{module_name}' not found in registry")

        # Dispatch based on action type
        if action_type == "block_ip":
            return await self._execute_block_ip(module, target, params)
        elif action_type == "unblock_ip":
            return await self._execute_unblock_ip(module, target, params)
        elif action_type == "isolate_host":
            return await self._execute_isolate_host(module, target, params)
        elif action_type == "terminate_process":
            return await self._execute_terminate_process(module, target, params)
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def _execute_block_ip(
        self,
        module: Any,
        target: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute IP blocking action."""
        reason = params.get("reason", "Human-approved block")
        duration = params.get("duration")  # Optional duration in seconds

        # Call module method (assuming it has block_ip_direct for approved actions)
        if hasattr(module, "block_ip_direct"):
            success = await module.block_ip_direct(
                ip=target,
                reason=reason,
                duration=duration,
            )
        elif hasattr(module, "_blocked_ips"):
            # Fallback: directly add to blocked set
            module._blocked_ips.add(target)
            success = True
        else:
            raise ValueError(f"Module {module.name} does not support block_ip")

        return {
            "success": success,
            "action": "block_ip",
            "target": target,
            "reason": reason,
            "duration": duration,
        }

    async def _execute_unblock_ip(
        self,
        module: Any,
        target: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute IP unblocking action."""
        if hasattr(module, "unblock_ip"):
            success = await module.unblock_ip(ip=target)
        elif hasattr(module, "_blocked_ips"):
            module._blocked_ips.discard(target)
            success = True
        else:
            raise ValueError(f"Module {module.name} does not support unblock_ip")

        return {
            "success": success,
            "action": "unblock_ip",
            "target": target,
        }

    async def _execute_isolate_host(
        self,
        module: Any,
        target: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute host isolation action."""
        # This would typically involve firewall rules or network isolation
        if hasattr(module, "isolate_host"):
            success = await module.isolate_host(hostname=target, **params)
        else:
            # Not implemented - log and return failure
            logger.warning("isolate_host_not_implemented", module=module.name)
            return {
                "success": False,
                "action": "isolate_host",
                "target": target,
                "error": "Not implemented in module",
            }

        return {
            "success": success,
            "action": "isolate_host",
            "target": target,
        }

    async def _execute_terminate_process(
        self,
        module: Any,
        target: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute process termination action."""
        if hasattr(module, "terminate_process"):
            success = await module.terminate_process(pid=target, **params)
        else:
            logger.warning("terminate_process_not_implemented", module=module.name)
            return {
                "success": False,
                "action": "terminate_process",
                "target": target,
                "error": "Not implemented in module",
            }

        return {
            "success": success,
            "action": "terminate_process",
            "target": target,
        }

    async def execute_by_id(self, pending_action_id: UUID) -> dict[str, Any]:
        """
        Execute an action by its ID.

        Convenience method that fetches and executes.

        Args:
            pending_action_id: The pending action ID

        Returns:
            Execution result

        Raises:
            ValueError: If action not found or not approved
        """
        action = await self.pending_action_repo.get(pending_action_id)

        if not action:
            raise ValueError(f"Pending action {pending_action_id} not found")

        if action.status not in ("approved", "expired"):
            raise ValueError(
                f"Cannot execute action in status: {action.status}. "
                f"Only approved or expired (with auto_action=approve) can be executed."
            )

        return await self.execute(action)
