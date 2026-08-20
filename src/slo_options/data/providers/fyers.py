from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fyers_apiv3 import fyersModel

from slo_options.data.providers.base import MarketDataProvider
from slo_options.models.market import OptionQuote, OptionType, Underlying


IST = ZoneInfo("Asia/Kolkata")


class FyersMarketDataProvider(MarketDataProvider):
    """Read-only FYERS API v3 market-data adapter for SLO research/paper trading."""

    def __init__(
        self,
        app_id: str | None = None,
        access_token: str | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        self.app_id = app_id or os.getenv("FYERS_APP_ID")
        self.access_token = access_token or os.getenv("FYERS_ACCESS_TOKEN")
        if not self.app_id:
            raise ValueError("FYERS_APP_ID is required for FYERS mode")
        if not self.access_token:
            raise ValueError("FYERS_ACCESS_TOKEN is required for FYERS mode")

        self.underlying_symbols = self._load_symbols()
        self.timeout_seconds = timeout_seconds
        self.client = fyersModel.FyersModel(
            client_id=self.app_id,
            token=self.access_token,
            is_async=False,
            log_path="",
        )

    @staticmethod
    def _load_symbols() -> dict[str, str]:
        default = {
            "NIFTY": "NSE:NIFTY50-INDEX",
            "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
        }
        raw = os.getenv("SLO_FYERS_SYMBOLS")
        if not raw:
            return default
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("SLO_FYERS_SYMBOLS must be valid JSON") from exc
        if not isinstance(value, dict) or not value:
            raise ValueError("SLO_FYERS_SYMBOLS must contain at least one symbol")
        return {str(k): str(v) for k, v in value.items()}

    def _symbol(self, symbol: str) -> str:
        try:
            return self.underlying_symbols[symbol]
        except KeyError as exc:
            raise KeyError(
                f"No FYERS symbol mapping for {symbol!r}. "
                "Add it to SLO_FYERS_SYMBOLS."
            ) from exc

    @staticmethod
    def _check(response: Any, operation: str) -> dict[str, Any]:
        if not isinstance(response, dict):
            raise RuntimeError(f"FYERS {operation} returned unexpected response: {response}")
        if response.get("s") != "ok":
            raise RuntimeError(f"FYERS {operation} failed: {response}")
        return response

    def get_underlying(self, symbol: str) -> Underlying:
        response = self._check(
            self.client.quotes(data={"symbols": self._symbol(symbol)}),
            f"quotes for {symbol}",
        )
        rows = response.get("d") or []
        if not rows:
            raise RuntimeError(f"FYERS returned no quote for {symbol}")
        values = rows[0].get("v", {})
        spot = float(values.get("lp") or 0)
        if spot <= 0:
            raise RuntimeError(f"FYERS returned invalid spot for {symbol}: {response}")
        return Underlying(symbol=symbol, spot=spot, timestamp=datetime.now(IST).replace(tzinfo=None))

    def get_option_chain(self, underlying: str, expiry: datetime | None = None) -> list[OptionQuote]:
        """Return a normalized option chain using the FYERS API v3 option-chain endpoint."""
        data: dict[str, Any] = {
            "symbol": self._symbol(underlying),
            "strikecount": 20,
        }
        if expiry is not None:
            data["timestamp"] = int(expiry.timestamp())

        response = self._check(self.client.optionchain(data=data), "option-chain")
        rows = (response.get("data") or {}).get("optionsChain") or []
        result: list[OptionQuote] = []

        for row in rows:
            option_symbol = row.get("symbol")
            if not option_symbol:
                continue

            option_type_value = str(row.get("option_type", "CE")).upper()
            option_type = (
                OptionType.CALL
                if option_type_value in {"CE", "CALL"}
                else OptionType.PUT
            )

            bid = float(row.get("bid", row.get("bid_price", 0)) or 0)
            ask = float(row.get("ask", row.get("ask_price", 0)) or 0)
            ltp = float(row.get("ltp", 0) or 0)
            if bid <= 0 or ask <= 0:
                continue

            expiry_value = row.get("expiry")
            if isinstance(expiry_value, (int, float)):
                exp = datetime.fromtimestamp(float(expiry_value), tz=IST).replace(tzinfo=None)
            elif expiry_value:
                exp = datetime.fromisoformat(str(expiry_value).replace("Z", "+00:00"))
                if exp.tzinfo is not None:
                    exp = exp.astimezone(IST).replace(tzinfo=None)
            elif expiry is not None:
                exp = expiry.replace(tzinfo=None) if expiry.tzinfo else expiry
            else:
                exp = datetime.now(IST).replace(tzinfo=None)

            result.append(
                OptionQuote(
                    underlying=underlying,
                    symbol=str(option_symbol),
                    strike=float(row.get("strike_price", row.get("strike", 0)) or 0),
                    option_type=option_type,
                    expiry=exp,
                    bid=bid,
                    ask=ask,
                    last=ltp if ltp > 0 else None,
                    volume=int(row.get("volume", 0) or 0),
                    open_interest=int(row.get("oi", row.get("open_interest", 0)) or 0),
                    implied_volatility=(
                        float(row["iv"]) / 100.0 if row.get("iv") is not None else None
                    ),
                )
            )
        return result

    def get_historical_closes(self, symbol: str, days: int = 80) -> list[tuple[datetime, float]]:
        """Return daily underlying closes from the FYERS History API."""
        end = datetime.now(IST)
        start = end - timedelta(days=max(days * 2, 30))
        response = self._check(
            self.client.history(
                data={
                    "symbol": self._symbol(symbol),
                    "resolution": "D",
                    "date_format": "0",
                    "range_from": int(start.timestamp()),
                    "range_to": int(end.timestamp()),
                    "cont_flag": "1",
                }
            ),
            f"history for {symbol}",
        )

        result: list[tuple[datetime, float]] = []
        for candle in response.get("candles") or []:
            if len(candle) < 5:
                continue
            timestamp = datetime.fromtimestamp(float(candle[0]), tz=IST).replace(tzinfo=None)
            result.append((timestamp, float(candle[4])))
        return sorted(result, key=lambda item: item[0])[-days:]
