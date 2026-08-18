from datetime import datetime
from slo_options.paper.ledger import PaperLedger, PaperTrade


class PaperTradingService:
    def __init__(self, ledger: PaperLedger | None = None) -> None:
        self.ledger = ledger or PaperLedger()

    def open_trade(
        self,
        trade_id: str,
        underlying: str,
        option_symbol: str,
        quantity: int,
        entry_price: float,
        stop_price: float,
        target_price: float,
    ) -> PaperTrade:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if entry_price <= 0 or stop_price <= 0 or target_price <= 0:
            raise ValueError("prices must be positive")
        if stop_price >= entry_price:
            raise ValueError("stop must be below entry for a long option")
        if target_price <= entry_price:
            raise ValueError("target must be above entry for a long option")

        trade = PaperTrade(
            trade_id=trade_id,
            timestamp=datetime.now(),
            underlying=underlying,
            option_symbol=option_symbol,
            side="BUY",
            quantity=quantity,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
        )
        self.ledger.add(trade)
        return trade

    def on_price(self, trade_id: str, price: float) -> str | None:
        for trade in self.ledger.trades:
            if trade.trade_id != trade_id:
                continue
            if trade.exit_price is not None:
                return None
            if price <= trade.stop_price:
                self.ledger.close(trade_id, price, "STOP")
                return "STOP"
            if price >= trade.target_price:
                self.ledger.close(trade_id, price, "TARGET")
                return "TARGET"
            return None
        raise KeyError(f"Trade {trade_id} not found")
