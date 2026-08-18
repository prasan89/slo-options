from datetime import datetime

from slo_options.paper.ledger import PaperLedger, PaperTrade
from slo_options.paper.report import build_report
from slo_options.paper.service import PaperTradingService


def test_paper_trade_target():
    service = PaperTradingService()
    service.open_trade("T1", "NIFTY", "NIFTY-25000-CE", 50, 100, 65, 150)

    reason = service.on_price("T1", 150)

    assert reason == "TARGET"
    assert service.ledger.realized_pnl() == 2500


def test_paper_trade_stop():
    service = PaperTradingService()
    service.open_trade("T2", "NIFTY", "NIFTY-25000-PE", 50, 100, 65, 150)

    reason = service.on_price("T2", 65)

    assert reason == "STOP"
    assert service.ledger.realized_pnl() == -1750


def test_paper_report():
    ledger = PaperLedger()
    ledger.add(PaperTrade("W", datetime.now(), "NIFTY", "X", "BUY", 1, 100, 65, 150, 150, "TARGET"))
    ledger.add(PaperTrade("L", datetime.now(), "NIFTY", "Y", "BUY", 1, 100, 65, 150, 65, "STOP"))

    report = build_report(ledger.trades)

    assert report.closed_trades == 2
    assert report.pnl == 50
    assert report.win_rate == 0.5
    assert report.profit_factor > 1
