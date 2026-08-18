# SLO Options V1

Systematic Long Options research platform.

## Strategy scope
- Long CALL / Long PUT only
- No option selling
- NIFTY + BANKNIFTY + liquid F&O stocks
- Target: research toward an average ₹50K/day objective; no forced daily trading quota
- Historical validation -> one-month forward paper trading -> small live deployment only after validation

## Architecture
Data Provider -> Normalized Models -> Analytics -> Strategy -> Risk -> Backtest -> Optimization -> Paper Trading -> MCP

## Data providers
- Mock provider for development
- **Upstox read-only provider** for real market data
- **Groww read-only provider** for real market data and historical F&O research

Groww's documented APIs provide live quotes, option chains with Greeks, and F&O historical backtesting data through expiry -> contract -> historical-candle APIs. F&O historical data is documented from 2020 onward. citeturn225452view0turn225452view1

## Current implementation
- Market/option models
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
- Real-data paper scan runner
- Real-data paper loop, 09:15-15:30 IST
- Provider factory for mock/upstox/groww
- MCP application facade

## Upstox real-data setup
```bash
DATA_PROVIDER=upstox
UPSTOX_ACCESS_TOKEN=YOUR_TOKEN
SLO_UNDERLYING_KEYS={"NIFTY":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank"}
```

## Groww real-data setup
Groww's current API documentation describes access-token authentication and a read-only live-data/option-chain flow. The access token is generated from Groww's Trading APIs area and expires daily at 6:00 AM. citeturn325644search4

```bash
DATA_PROVIDER=groww
GROWW_ACCESS_TOKEN=YOUR_TOKEN
SLO_GROWW_UNDERLYING_SYMBOLS={"NIFTY":"NIFTY","BANKNIFTY":"BANKNIFTY"}
```

Do not commit real tokens or `.env` to GitHub.

## Paper account
```bash
SLO_PAPER_CAPITAL=1500000
SLO_PAPER_TRADE_ALLOCATION=150000
SLO_PAPER_INTERVAL_SECONDS=300
```

The current paper test allocates up to ₹1.5 lakh to a selected trade from a ₹15 lakh paper account, subject to whole-lot sizing. Stop-loss risk is reported separately.

## Run a real-data paper scan
```bash
python -m slo_options.paper.real_scan
```

or:

```bash
slo-paper-scan
```

## Run continuous paper trading
```bash
slo-paper-loop
```

The loop uses the configured read-only provider and never sends broker orders. It runs only during the NSE market window **09:15-15:30 IST**, does not open new positions after 15:30, and closes remaining paper positions at end of day using the latest available bid.

## Historical option research with Groww
Groww documents an expiry -> contract -> historical candle workflow for F&O options, including CE/PE contract symbols and historical candles. This will be used to build the real option-history backtest dataset rather than relying on synthetic data. citeturn225452view1

## Local setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Important
This repository is for research, backtesting and paper trading. It does not place live orders.
