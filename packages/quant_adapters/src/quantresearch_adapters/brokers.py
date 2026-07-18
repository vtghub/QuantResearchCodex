from typing import Any

from quantresearch_core.contracts import BrokerMode, OrderIntent


class BrokerAdapterDisabledError(RuntimeError):
    """Raised when a live broker adapter is invoked before enablement gates exist."""


class BaseBrokerAdapter:
    name: str

    def __init__(
        self,
        mode: BrokerMode = BrokerMode.PAPER,
        live_trading_enabled: bool = False,
    ) -> None:
        self.mode = mode
        self.live_trading_enabled = live_trading_enabled

    async def submit_order(self, order: OrderIntent) -> dict[str, Any]:
        if self.mode == BrokerMode.LIVE and not self.live_trading_enabled:
            raise BrokerAdapterDisabledError(
                "Live trading is disabled until paper/sandbox gates pass."
            )
        return {
            "broker": self.name,
            "mode": self.mode,
            "client_order_id": order.client_order_id,
            "status": "accepted-paper" if self.mode == BrokerMode.PAPER else "accepted-live",
        }

    async def reconcile(self) -> dict[str, Any]:
        return {"broker": self.name, "mode": self.mode, "status": "placeholder"}


class AlpacaBrokerAdapter(BaseBrokerAdapter):
    name = "alpaca"


class InteractiveBrokersAdapter(BaseBrokerAdapter):
    name = "interactive-brokers"
