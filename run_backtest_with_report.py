"""
Run backtest with full report generation.
Saves summary text and graphs to backtest_reports folder.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data import DataManager
from strategy.rsi_strategy import RSIStrategy
from backtest.engine import Backtester
from backtest.report import BacktestReport
from risk.position_sizer import PositionSizingConfig


def run_with_report(
    symbol: str,
    start: str,
    end: str,
    strategy_name: str,
    strategy,
    sizing_config: PositionSizingConfig,
    sizing_method: str,
    initial_capital: float = 100000.0
):
    """Run a backtest and generate full report."""
    dm = DataManager()
    
    print(f"\nFetching data for {symbol}...")
    data = dm.fetch_data(symbol, period="1d", start_time=start, end_time=end)
    
    if data is None or data.empty:
        print("ERROR: No data")
        return None
    
    print(f"Data: {len(data)} bars from {data.index[0].date()} to {data.index[-1].date()}")
    
    # Run backtest
    print(f"\nRunning backtest: {strategy_name} ({sizing_method})...")
    backtester = Backtester(
        data=data,
        strategy=strategy,
        initial_capital=initial_capital,
        sizing_config=sizing_config
    )
    backtester.run()
    results = backtester.get_results()
    
    # Generate report
    reporter = BacktestReport(output_dir="backtest_reports")
    report_dir = reporter.generate_report(
        results=results,
        data=data,
        strategy_name=strategy_name,
        symbol=symbol,
        sizing_method=sizing_method,
        initial_capital=initial_capital
    )
    
    return results, report_dir


def main():
    print("=" * 70)
    print("BACKTEST WITH REPORT GENERATION")
    print("=" * 70)
    
    # Test 1: RSI All-In on 510050.SH
    strategy1 = RSIStrategy(period=14, overbought=70, oversold=30)
    run_with_report(
        symbol="510050.SH",
        start="20100101",
        end="20201231",
        strategy_name="RSI",
        strategy=strategy1,
        sizing_config=PositionSizingConfig(method="all_in"),
        sizing_method="all_in"
    )
    
    # Test 2: RSI Fixed-Fraction on 510050.SH
    strategy2 = RSIStrategy(period=14, overbought=70, oversold=30)
    run_with_report(
        symbol="510050.SH",
        start="20100101",
        end="20201231",
        strategy_name="RSI",
        strategy=strategy2,
        sizing_config=PositionSizingConfig(method="fixed_fraction", fraction=1.0, min_cash_fraction=0.4),
        sizing_method="fixed_fraction_40pct"
    )
    
    # Test 3: RSI on 510300.SH
    strategy3 = RSIStrategy(period=14, overbought=70, oversold=30)
    run_with_report(
        symbol="510300.SH",
        start="20100101",
        end="20201231",
        strategy_name="RSI",
        strategy=strategy3,
        sizing_config=PositionSizingConfig(method="all_in"),
        sizing_method="all_in"
    )
    
    print("\n" + "=" * 70)
    print("All reports saved to: backtest_reports/")
    print("=" * 70)


if __name__ == "__main__":
    main()
