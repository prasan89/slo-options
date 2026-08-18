import os
from datetime import date, datetime, timedelta
from typing import Any

import requests

from slo_options.data.providers.base import MarketDataProvider
from slo_options.models.market import OptionQuote, OptionType, Underlying


class UpstoxMarketDataProvider(MarketDataProvider):
    """Real NSE market-data adapter using the Upstox REST API.

    This adapter is read-only. It never places orders.
    """

    BASE_URL = "https://api.upstox.com/v2"
    HIST_BASE_URL = "https://api.upstox.com/v3"

    def __init__(
        self,
        access_token: str | None = None,
        underlying_keys: dict[str, str] | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        self.access_token = access_token or os.getenv("UPSTOX_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("UPSTOX_ACCESS_TOKEN is required for real-data mode")

        self.underlying_keys = underlying_keys or self._load_underlying_keys()
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            }
        )

    @staticmethod
    def _load_underlying_keys() -> dict[str, str]:
        # Example:
        # SLO_UNDERLYING_KEYS='{"NIFTY":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank"}'
        import json

        raw = os.getenv("SLO_UNDERLYING_KEYS", "{}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("SLO_UNDERLYING_KEYS must be valid JSON") from exc
        if not isinstance(value, dict) or not value:
            raise ValueError("SLO_UNDERLYING_KEYS must contain at least one symbol mapping")
        return {str(k): str(v) for k, v in value.items()}

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(
            f"{self.BASE_URL}{path}",
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") not in (None, "success"):
            raise RuntimeError(f"Upstox API returned status={payload.get('status')}")
        return payload

    def _key(self, symbol: str) -> str:
        try:
            return self.underlying_keys[symbol]
        except KeyError as exc:
            raise KeyError(
                f"No Upstox instrument key configured for {symbol}. "
                "Add it to SLO_UNDERLYING_KEYS."
            ) from exc

    def get_underlying(self, symbol: str) -> Underlying:
        key = self._key(symbol)
        payload = self._request("/market-quote/quotes", {"instrument_key": key})
        data = next(iter(payload["data"].values()))
        spot = float(data["last_price"])
        timestamp = datetime.fromtimestamp(float(data.get("last_trade_time", 0)) / 1000) if data.get("last_trade_time") else datetime.now()
        return Underlying(symbol=symbol, spot=spot, timestamp=timestamp)

    def get_option_chain(
        self,
        underlying: str,
        expiry: datetime | None = None,
    ) -> list[OptionQuote]:
        key = self._key(underlying)
        expiry_date = (expiry.date() if expiry else None)
        expiry_value = expiry_date.isoformat() if expiry_date else "current_week"
        payload = self._request(
            "/option/chain",
            {"instrument_key": key, "expiry_date": expiry_value},
        )

        options: list[OptionQuote] = []
        for row in payload.get("data", []):
            expiry_dt = datetime.fromisoformat(row["expiry"])
            strike = float(row["strike_price"])
            for typ, field in ((OptionType.CALL, "call_options"), (OptionType.PUT, "put_options")):
                contract = row.get(field) or {}
                market = contract.get("market_data") or {}
                greeks = contract.get("option_greeks") or {}
                if not contract or market.get("bid_price") is None or market.get("ask_price") is None:
                    continue

                options.append(
                    OptionQuote(
                        underlying=underlying,
                        symbol=str(contract.get("instrument_key")),
                        strike=strike,
                        option_type=typ,
                        expiry=expiry_dt,
                        bid=float(market.get("bid_price", 0)),
                        ask=float(market.get("ask_price", 0)),
                        last=float(market["ltp"]) if market.get("ltp") is not None else None,
                        volume=int(market.get("volume", 0)),
                        open_interest=int(market.get("oi", 0)),
                        implied_volatility=float(greeks["iv"]) / 100.0 if greeks.get("iv") is not None and float(greeks["iv"]) > 2 else (float(greeks["iv"]) if greeks.get("iv") is not None else None),
                    )
                )

        return options

    def get_historical_closes(
        self,
        symbol: str,
        days: int = 80,
    ) -> list[tuple[datetime, float]]:
        """Return daily closes for the configured underlying."""
        key = self._key(symbol)
        to_date = date.today()
        from_date = to_date - timedelta(days=days * 2)
        encoded_key = key.replace("|", "%7C").replace(" ", "%20")
        url = (
            f"{self.HIST_BASE_URL}/historical-candle/{encoded_key}/days/1/"
            f"{to_date.isoformat()}/{from_date.isoformat()}"
        )
        response = self.session.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        candles = payload.get("data", {}).get("candles", [])
        result = []
        for candle in candles:
            result.append((datetime.fromisoformat(candle[0]), float(candle[4])))
        return sorted(result, key=lambda x: x[0])[-days:]
