from quantresearch_adapters.brokers import (
    AlpacaBrokerAdapter,
    BrokerAdapterDisabledError,
    InteractiveBrokersAdapter,
)
from quantresearch_core.contracts import AssetClass, BrokerMode, Instrument, OrderIntent

from quantresearch_api.risk import risk_control_service
from quantresearch_api.schemas import BrokerOrderRequest, BrokerOrderResponse, TenantContext
from quantresearch_api.settings import Settings


class BrokerSandboxGateError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class BrokerSandboxService:
    def __init__(self) -> None:
        self._orders: dict[tuple[str, str, str], BrokerOrderResponse] = {}

    async def submit_order(
        self,
        broker_name: str,
        request: BrokerOrderRequest,
        context: TenantContext,
        settings: Settings,
    ) -> BrokerOrderResponse:
        normalized_broker = broker_name.lower()
        adapter = self._adapter(normalized_broker, request.mode, settings.live_trading_enabled)
        order_key = (
            str(context.tenant_id),
            normalized_broker,
            request.client_order_id,
        )
        if order_key in self._orders:
            replayed = self._orders[order_key].model_copy()
            replayed.gates = [*replayed.gates, "idempotency-replay"]
            return replayed

        gates = [
            *risk_control_service.ensure_execution_allowed(context),
            *self._evaluate_gates(request, settings),
        ]
        intent = self._build_intent(request, context)
        try:
            broker_result = await adapter.submit_order(intent)
        except BrokerAdapterDisabledError as exc:
            raise BrokerSandboxGateError(str(exc), status_code=403) from exc

        response = BrokerOrderResponse(
            broker=normalized_broker,
            mode=request.mode,
            client_order_id=request.client_order_id,
            status=str(broker_result["status"]),
            estimated_notional=request.estimated_notional,
            gates=gates,
        )
        self._orders[order_key] = response
        return response

    def _adapter(self, broker_name: str, mode: BrokerMode, live_enabled: bool):
        if broker_name == "alpaca":
            return AlpacaBrokerAdapter(mode=mode, live_trading_enabled=live_enabled)
        if broker_name in {"interactive-brokers", "ibkr"}:
            return InteractiveBrokersAdapter(mode=mode, live_trading_enabled=live_enabled)
        raise BrokerSandboxGateError(f"Unsupported broker: {broker_name}", status_code=404)

    def _evaluate_gates(self, request: BrokerOrderRequest, settings: Settings) -> list[str]:
        if request.mode != BrokerMode.PAPER:
            raise BrokerSandboxGateError(
                "Live orders are blocked until paper/sandbox gates and approvals pass.",
                status_code=403,
            )
        if request.estimated_notional > settings.paper_order_max_notional:
            raise BrokerSandboxGateError(
                "Paper order notional exceeds the sandbox limit.",
                status_code=422,
            )
        return [
            "mode-paper",
            "live-disabled",
            "idempotency-key-present",
            f"notional<={settings.paper_order_max_notional:.2f}",
        ]

    def _build_intent(self, request: BrokerOrderRequest, context: TenantContext) -> OrderIntent:
        return OrderIntent(
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            strategy_id=request.strategy_id,
            instrument=Instrument(
                symbol=request.symbol.upper(),
                asset_class=AssetClass(request.asset_class),
                venue=request.venue.upper(),
                currency=request.currency.upper(),
                timezone=request.timezone,
            ),
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            client_order_id=request.client_order_id,
            mode=request.mode,
        )


broker_sandbox_service = BrokerSandboxService()
