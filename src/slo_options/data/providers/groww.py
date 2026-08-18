import json
import os
from datetime import date, datetime, timedelta
from typing import Any

import requests

from slo_options.data.providers.base import MarketDataProvider
from slo_options.models.market import OptionQuote, OptionType, Underlying


class GrowwMarketDataProvider(MarketDataProvider):
    """Read-only Groww market-data adapter for live paper trading and research.

    Uses Groww's documented REST APIs for quotes, option chains and historical
    candles. It never places orders.
    """

    BASE_URL = "https://api.groww.in/v1"
    HEADERS = {"Accept": "application/json", "X-API-VERSION": "1.0"}

    def __init__(
        self,
        access_token: str | None = None,
        underlying_symbols: dict[str, str] | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        self.access_token = access_token or os.getenv("GROWW_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("GROWW_ACCESS_TOKEN is required for Groww mode")
        self.underlying_symbols = underlying_symbols or self._load_underlying_symbols()
        self.underlying_keys = self.underlying_symbols
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({**self.HEADERS, "Authorization": f"Bearer {self.access_token}"})

    @staticmethod
    def _load_underlying_symbols() -> dict[str, str]:
        raw = os.getenv("SLO_GROWW_UNDERLYING_SYMBOLS", "{}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("SLO_GROWW_UNDERLYING_SYMBOLS must be valid JSON") from exc
        if not isinstance(value, dict) or not value:
            raise ValueError("SLO_GROWW_UNDERLYING_SYMBOLS must contain at least one symbol")
        return {str(k): str(v) for k, v in value.items()}

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(f"{self.BASE_URL}{path}", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") not in (None, "SUCCESS"):
            raise RuntimeError(f"Groww API returned status={payload.get('status')}")
        return payload

    def _underlying_symbol(self, symbol: str) -> str:
        try:
            return self.underlying_symbols[symbol]
        except KeyError as exc:
            raise KeyError(f"No Groww underlying symbol configured for {symbol}") from exc

    def get_underlying(self, symbol: str) -> Underlying:
        trading_symbol = self._underlying_symbol(symbol)
        payload = self._request(
            "/live-data/quote",
            {"exchange": "NSE", "segment": "CASH", "trading_symbol": trading_symbol},
        )
        data = payload.get("payload", {})
        spot = float(data.get("last_price", 0))
        if spot <= 0:
            raise RuntimeError(f"Groww returned invalid spot for {symbol}")
        timestamp_ms = data.get("last_trade_time")
        timestamp = datetime.fromtimestamp(float(timestamp_ms) / 1000) if timestamp_ms else datetime.now()
        return Underlying(symbol=symbol, spot=spot, timestamp=timestamp)

    def _nearest_expiry(self, underlying: str) -> datetime:
        expiries = sorted(self.get_expiries(underlying, year=date.today().year, month=date.today().month))
        today = date.today()
        for expiry in expiries:
            if expiry >= today:
                return datetime.combine(expiry, datetime.min.time())
        next_month = today.month + 1
        next_year = today.year
        if next_month == 13:
            next_month, next_year = 1, next_year + 1
        future = sorted(self.get_expiries(underlying, year=next_year, month=next_month))
        for expiry in future:
            if expiry >= today:
                return datetime.combine(expiry, datetime.min.time())
        raise RuntimeError(f"No future Groww expiry found for {underlying}")

    def get_option_chain(self, underlying: str, expiry: datetime | None = None) -> list[OptionQuote]:
        expiry = expiry or self._nearest_expiry(underlying)
        payload = self._request(
            f"/option-chain/exchange/NSE/underlying/{self._underlying_symbol(underlying)}",
            {"expiry_date": expiry.date().isoformat()},
        )
        data = payload.get("payload", {})
        options: list[OptionQuote] = []

        for strike_text, strike_data in (data.get("strikes") or {}).items():
            strike = float(strike_text)
            for option_type, code in ((OptionType.CALL, "CE"), (OptionType.PUT, "PE")):
                contract = (strike_data or {}).get(code) or {}
                trading_symbol = contract.get("trading_symbol")
                if not trading_symbol:
                    continue

                quote_payload = self._request(
                    "/live-data/quote",
                    {"exchange": "NSE", "segment": "FNO", "trading_symbol": trading_symbol},
                )
                market = quote_payload.get("payload", {})
                greeks = contract.get("greeks") or {}
                bid = float(market.get("bid_price", 0) or 0)
                ask = float(market.get("offer_price", 0) or 0)
                ltp = float(contract.get("ltp", market.get("last_price", 0)) or 0)
                if bid <= 0 or ask <= 0:
                    continue

                iv = greeks.get("iv")
                iv_value = None if iv is None else float(iv) / 100.0
                options.append(
                    OptionQuote(
                        underlying=underlying,
                        symbol=trading_symbol,
                        strike=strike,
                        option_type=option_type,
                        expiry=expiry,
                        bid=bid,
                        ask=ask,
                        last=ltp if ltp > 0 else None,
                        volume=int(contract.get("volume", market.get("volume", 0)) or 0),
                        open_interest=int(contract.get("open_interest", market.get("open_interest", 0)) or 0),
                        implied_volatility=iv_value,
                    )
                )

        return options

    def get_expiries(self, underlying: str, year: int | None = None, month: int | None = None) -> list[date]:
        params: dict[str, Any] = {
            "exchange": "NSE",
            "underlying_symbol": self._underlying_symbol(underlying),
        }
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        payload = self._request("/historical/expiries", params)
        return [date.fromisoformat(x) for x in payload.get("payload", {}).get("expiries", [])]

    def get_contracts(self, underlying: str, expiry: date) -> list[str]:
        payload = self._request(
            "/historical/contracts",
            {
                "exchange": "NSE",
                "underlying_symbol": self._underlying_symbol(underlying),
                "expiry_date": expiry.isoformat(),
            },
        )
        return [str(x) for x in payload.get("payload", {}).get("contracts", [])]

    def get_historical_candles(
        self,
        groww_symbol: str,
        start_time: datetime,
        end_time: datetime,
        candle_interval: str = "15minute",
        segment: str = "FNO",
    ) -> list[list[Any]]:
        payload = self._request(
            "/historical/candles",
            {
                "exchange": "NSE",
                "segment": segment,
                "groww_symbol": groww_symbol,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "candle_interval": candle_interval,
            },
        )
        return list(payload.get("payload", {}).get("candles", []))

    def get_historical_closes(self, symbol: str, days: int = 80) -> list[tuple[datetime, float]]:
        end = datetime.now()
        start = end - timedelta(days=days * 2)
        candles = self.get_historical_candles(
            groww_symbol=f"NSE-{self._underlying_symbol(symbol)}",
            start_time=start,
            end_time=end,
            candle_interval="1day",
            segment="CASH",
        )
        result: list[tuple[datetime, float]] = []
        for candle in candles:
            if len(candle) < 5:
                continue
            timestamp = candle[0]
            dt = datetime.fromtimestamp(float(timestamp)) if isinstance(timestamp, (int, float)) else datetime.fromisoformat(str(timestamp))
            result.append((dt, float(candle[4])))
        return sorted(result, key=lambda x: x[0])[-days:]
