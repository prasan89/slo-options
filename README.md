# SLO Options V1

Systematic Long Options research platform.

Scope:
- Long CALL / Long PUT only
- No option selling
- NIFTY + BANKNIFTY + liquid F&O stocks
- Strategy, risk, backtesting and MCP layers will be added incrementally

Current milestone:
- Market data models
- Provider abstraction
- Mock provider
- Black-Scholes pricing
- Greeks
- IV solver
- HV and IV/HV
- Expected move
- Liquidity filters
- Candidate scoring

Install:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
