from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from quantresearch_api.schemas import (
    ApprovalDecisionResponse,
    ApprovalRecord,
    ApprovalRequest,
    KillSwitchRequest,
    KillSwitchState,
    RiskPolicySummary,
    TenantContext,
)


class RiskGateError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class _TenantRiskState:
    kill_switch: KillSwitchState
    approvals: dict[UUID, ApprovalRecord] = field(default_factory=dict)


class RiskControlService:
    def __init__(self) -> None:
        self._state: dict[UUID, _TenantRiskState] = {}

    def policies(self, context: TenantContext) -> list[RiskPolicySummary]:
        return [
            RiskPolicySummary(
                tenant_id=context.tenant_id,
                name="execution-kill-switch",
                status="armed" if self.kill_switch(context).enabled else "clear",
                scope="tenant",
                description="Blocks all broker order submission when enabled.",
            ),
            RiskPolicySummary(
                tenant_id=context.tenant_id,
                name="paper-notional-limit",
                status="active",
                scope="tenant",
                description="Caps paper order notional before broker adapter submission.",
            ),
            RiskPolicySummary(
                tenant_id=context.tenant_id,
                name="two-person-live-approval",
                status="modeled",
                scope="strategy",
                description="Requires separate requester and approver before live enablement.",
            ),
        ]

    def kill_switch(self, context: TenantContext) -> KillSwitchState:
        return self._tenant_state(context).kill_switch

    def set_kill_switch(
        self,
        request: KillSwitchRequest,
        context: TenantContext,
    ) -> KillSwitchState:
        state = KillSwitchState(
            tenant_id=context.tenant_id,
            enabled=request.enabled,
            reason=request.reason,
            updated_by=context.role,
            updated_at=datetime.now(UTC),
        )
        self._tenant_state(context).kill_switch = state
        return state

    def ensure_execution_allowed(self, context: TenantContext) -> list[str]:
        kill_switch = self.kill_switch(context)
        if kill_switch.enabled:
            raise RiskGateError(
                f"Execution is blocked by tenant kill switch: {kill_switch.reason}",
                status_code=423,
            )
        return ["kill-switch-clear"]

    def request_approval(
        self,
        request: ApprovalRequest,
        context: TenantContext,
    ) -> ApprovalRecord:
        record = ApprovalRecord(
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            target_kind=request.target_kind,
            target_id=request.target_id,
            requested_by=context.role,
            reason=request.reason,
        )
        self._tenant_state(context).approvals[record.id] = record
        return record

    def approvals(self, context: TenantContext) -> list[ApprovalRecord]:
        return list(self._tenant_state(context).approvals.values())

    def approve(
        self,
        approval_id: UUID,
        context: TenantContext,
    ) -> ApprovalDecisionResponse:
        approvals = self._tenant_state(context).approvals
        if approval_id not in approvals:
            raise RiskGateError("Approval request not found.", status_code=404)

        record = approvals[approval_id]
        if context.role == record.requested_by:
            raise RiskGateError("Requester cannot approve their own request.", status_code=409)
        if context.role not in record.approved_by:
            record.approved_by.append(context.role)
        record.status = "approved"
        record.decided_at = datetime.now(UTC)
        return ApprovalDecisionResponse(record=record, gates=["two-person-approval-satisfied"])

    def _tenant_state(self, context: TenantContext) -> _TenantRiskState:
        if context.tenant_id not in self._state:
            self._state[context.tenant_id] = _TenantRiskState(
                kill_switch=KillSwitchState(
                    tenant_id=context.tenant_id,
                    enabled=False,
                    reason="default-clear",
                    updated_by="system",
                )
            )
        return self._state[context.tenant_id]


risk_control_service = RiskControlService()
