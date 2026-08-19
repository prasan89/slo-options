import json
import os
from datetime import date, datetime, timedelta
from typing import Any

import requests

from slo_options.data.providers.base import MarketDataProvider
from slo_options.models.market import OptionQuote, OptionType, Underlying


class FyersMarketDataProvider(MarketDataProvider):
    """Read-only FYERS REST market-data adapter for SLO research/paper trading."""

    BASE_URL = "https://api-t1.fyers.in/data"

    def __init__(self, access_token: str | None = None, timeout_seconds: int = 15) -> None:
        self.access_token = access_token or os.getenv("FYERS_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("FYERS_ACCESS_TOKEN is required for FYERS mode")
        self.underlying_symbols = self._load_symbols()
        self.underlying_keys = self.underlying_symbols
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.access_token, "Content-Type": "application/json"})

    @staticmethod
    def _load_symbols() -> dict[str, str]:
        raw = os.getenv("SLO_FYERS_SYMBOLS", "{}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("SLO_FYERS_SYMBOLS must be valid JSON") from exc
        if not isinstance(value, dict) or not value:
            raise ValueError("SLO_FYERS_SYMBOLS must contain at least one symbol")
        return {str(k): str(v) for k, v in value.items()}

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(f"{self.BASE_URL}{path}", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if payload.get("s") not in (None, "ok"):
            raise RuntimeError(f"FYERS API error: {payload}")
        return payload

    def get_underlying(self, symbol: str) -> Underlying:
        trading_symbol = self.underlying_symbols[symbol]
        payload = self._get("/quotes", {"symbols": trading_symbol})
        item = payload.get("d", [{}])[0]
        values = item.get("v", {})
        spot = float(values.get("lp", 0))
        if spot <= 0:
            raise RuntimeError(f"FYERS returned invalid spot for {symbol}")
        return Underlying(symbol=symbol, spot=spot, timestamp=datetime.now())

    def get_option_chain(self, underlying: str, expiry: datetime | None = None) -> list[OptionQuote]:
        """Return a normalized chain from FYERS option-chain response.

        FYERS symbol mappings are intentionally configuration-driven because
        option symbol formats and expiry contracts change over time.
        """
        chain_symbol = self.underlying_symbols[underlying]
        params: dict[str, Any] = {"symbol": chain_symbol, "strikecount": 20}
        if expiry is not None:
            params["timestamp"] = int(expiry.timestamp())
        payload = self._get("/option-chain", params)
        rows = payload.get("data", {}).get("optionsChain", [])
        result: list[OptionQuote] = []
        for row in rows:
            option_symbol = row.get("symbol")
            if not option_symbol:
                continue
            option_type = OptionType.CALL if str(row.get("option_type", "CE")).upper() in {"CE", "CALL"} else OptionType.PUT
            bid = float(row.get("bid", row.get("bid_price", 0)) or 0)
            ask = float(row.get("ask", row.get("ask_price", 0)) or 0)
            ltp = float(row.get("ltp", 0) or 0)
            if bid <= 0 or ask <= 0:
                continue
            expiry_value = row.get("expiry")
            if isinstance(expiry_value, (int, float)):
                exp = datetime.fromtimestamp(float(expiry_value))
            elif expiry_value:
                exp = datetime.fromisoformat(str(expiry_value))
            elif expiry is not None:
                exp = expiry
            else:
                exp = datetime.now()
            result.append(
                OptionQuote(
                    underlying=underlying,
                    symbol=option_symbol,
                    strike=float(row.get("strike_price", row.get("strike", 0)) or 0),
                    option_type=option_type,
                    expiry=exp,
                    bid=bid,
                    ask=ask,
                    last=ltp if ltp > 0 else None,
                    volume=int(row.get("volume", 0) or 0),
                    open_interest=int(row.get("oi", row.get("open_interest", 0)) or 0),
                    implied_volatility=(float(row["iv"]) / 100.0 if row.get("iv") is not None else None),
                )
            )
        return result

    def get_historical_closes(self, symbol: str, days: int = 80) -> list[tuple[datetime, float]]:
        end = datetime.now()
        start = end - timedelta(days=days * 2)
        payload = self._get(
            "/history",
            {
                "symbol": self.underlying_symbols[symbol],
                "resolution": "D",
                "date_format": "1",
                "range_from": start.strftime("%Y-%m-%d"),
                "range_to": end.strftime("%Y-%m-%d"),
                "cont_flag": "1",
            },
        )
        result: list[tuple[datetime, float]] = []
        for candle in payload.get("candles", []):
            if len(candle) < 5:
                continue
            result.append((datetime.fromtimestamp(float(candle[0])), float(candle[4])))
        return sorted(result, key=lambda x: x[0])[-days:]
