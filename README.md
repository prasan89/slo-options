# SLO Options V1

Systematic Long Options research platform.

## Strategy scope
- Long CALL / Long PUT only
- No option selling
- NIFTY + BANKNIFTY + liquid F&O stocks
- Target: research toward an average ₹10K/day objective; no forced daily trading quota
- Historical validation -> one-month forward paper trading -> small live deployment only after validation

## Architecture
Data Provider -> Normalized Models -> Analytics -> Strategy -> Risk -> Backtest -> Optimization -> Paper Trading -> MCP

## Current implementation
- Market/option models
- Mock market-data provider
- **Real Upstox market-data provider (read-only)**
- Black-Scholes option pricing
- Delta, Gamma, Theta, Vega
- Implied-volatility solver
- Historical volatility and IV/HV
- Expected move
- Breakeven
- Liquidity filtering
- Candidate scoring
- V1 directional score
- Long-only CALL/PUT selector
- Entry stop/target calculation
- Risk limits and position sizing
- Backtesting engine
- Slippage/commission model
- P&L, drawdown and trade metrics
- Parameter grid optimization
- Walk-forward and robustness utilities
- Paper trading ledger/service/reporting
- **Real-data paper scan runner**
- MCP application facade

## Real-data setup
The current real-data adapter uses Upstox REST APIs for the option chain and market quotes. TradingView remains useful for visual analysis, but its official documentation says it does not currently provide a general API for programmatic data access. citeturn965535search1

Create an Upstox developer app and obtain an access token. Upstox uses OAuth 2.0, and its access tokens expire at 3:30 AM the following day. citeturn856176search0turn856176search2

Copy `.env.example` to `.env` and configure:

```bash
DATA_PROVIDER=upstox
UPSTOX_ACCESS_TOKEN=YOUR_TOKEN
SLO_UNDERLYING_KEYS={"NIFTY":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank"}
SLO_LOT_SIZES={"NIFTY":1,"BANKNIFTY":1}
```

The Upstox option-chain endpoint returns expiry, spot, bid/ask, volume, OI and option Greeks including IV, delta, gamma, theta and vega. citeturn965535search2

## Run a real-data paper scan

```bash
python -m slo_options.paper.real_scan
```

or, after installation:

```bash
slo-paper-scan
```

The scanner writes `reports/paper_signals.csv` and **does not place any orders**.

## Historical data
Upstox also exposes expired option contracts and expired historical candles, which gives us a path toward real option-history backtesting. citeturn856176search1turn856176search3turn856176search9

## Local setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Important
This repository is for research, backtesting and paper trading. It does not place live orders.
