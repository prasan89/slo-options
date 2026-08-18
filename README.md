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
- Market-data provider abstraction
- Mock provider for development
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
- Paper trading ledger
- Paper trading service
- Paper performance report
- MCP application facade

## Local setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Important
This repository is for research, backtesting and paper trading. It does not place live orders.
