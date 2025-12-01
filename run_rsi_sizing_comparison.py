"""
Compare RSI strategy performance on 510300.SH (2010-2020)
using two position sizing modes:
  1. All-in (legacy behavior)
  2. Fixed-fraction with 40% cash reserve

Run this script from the project root:
    python run_rsi_sizing_comparison.py
"""

import sys
import os

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
from datetime import datetime

from data import DataManager
from strategy.rsi_strategy import RSIStrategy
from backtest.engine import Backtester
from risk.position_sizer import PositionSizingConfig


def run_backtest(data: pd.DataFrame, sizing_config: PositionSizingConfig, label: str):
    """Run a single backtest and return results dict."""
    strategy = RSIStrategy(period=14, overbought=70, oversold=30)
    backtester = Backtester(
        data=data,
        strategy=strategy,
        initial_capital=100000.0,
        commission_rate=0.0003,
        stamp_duty=0.001,
        slippage=0.0,
        sizing_config=sizing_config,
    )
    print(f"\n{'='*60}")
    print(f"Running backtest: {label}")
    print(f"{'='*60}")
    backtester.run()
    results = backtester.get_results()
    return results


def main():
    # -------------------------------------------------------------------------
    # 1. Fetch data for 510300.SH (CSI 300 ETF) from 2010 to 2020
    # -------------------------------------------------------------------------
    dm = DataManager()
    symbol = "510300.SH"
    start_date = "20100101"
    end_date = "20201231"

    print(f"Fetching daily data for {symbol} from {start_date} to {end_date}...")
    data = dm.fetch_data(symbol, period="1d", start_time=start_date, end_time=end_date)

    if data is None or data.empty:
        print("ERROR: Could not fetch data. Exiting.")
        return

    print(f"Data loaded: {len(data)} bars from {data.index[0]} to {data.index[-1]}")

    # -------------------------------------------------------------------------
    # 2. Define sizing configs
    # -------------------------------------------------------------------------
    config_all_in = PositionSizingConfig(method="all_in")

    config_fixed_fraction = PositionSizingConfig(
        method="fixed_fraction",
        fraction=1.0,            # use all allocatable cash above reserve
        min_cash_fraction=0.4,   # keep 40% of initial capital as cash
        lot_size=100,
    )

    # -------------------------------------------------------------------------
    # 3. Run backtests
    # -------------------------------------------------------------------------
    results_all_in = run_backtest(data, config_all_in, "All-In (legacy)")
    results_fixed = run_backtest(data, config_fixed_fraction, "Fixed-Fraction (40% cash reserve)")

    # -------------------------------------------------------------------------
    # 4. Compare metrics
    # -------------------------------------------------------------------------
    metrics_all_in = results_all_in["metrics"]
    metrics_fixed = results_fixed["metrics"]

    print("\n")
    print("=" * 70)
    print("COMPARISON: All-In vs Fixed-Fraction (40% cash reserve)")
    print("=" * 70)
    print(f"{'Metric':<30} {'All-In':>18} {'Fixed-Fraction':>18}")
    print("-" * 70)

    all_keys = set(metrics_all_in.keys()) | set(metrics_fixed.keys())
    for key in sorted(all_keys):
        val_a = metrics_all_in.get(key, "N/A")
        val_f = metrics_fixed.get(key, "N/A")

        # Format numbers nicely
        def fmt(v):
            if isinstance(v, float):
                if abs(v) < 0.0001:
                    return f"{v:.6f}"
                return f"{v:.4f}"
            return str(v)

        print(f"{key:<30} {fmt(val_a):>18} {fmt(val_f):>18}")

    print("-" * 70)

    # -------------------------------------------------------------------------
    # 5. Trade counts
    # -------------------------------------------------------------------------
    trades_all_in = results_all_in.get("trades", pd.DataFrame())
    trades_fixed = results_fixed.get("trades", pd.DataFrame())

    n_trades_all_in = len(trades_all_in)
    n_trades_fixed = len(trades_fixed)

    print(f"{'Closed Trades':<30} {n_trades_all_in:>18} {n_trades_fixed:>18}")

    # -------------------------------------------------------------------------
    # 6. Final equity
    # -------------------------------------------------------------------------
    hist_all_in = results_all_in.get("history", pd.DataFrame())
    hist_fixed = results_fixed.get("history", pd.DataFrame())

    final_equity_all_in = hist_all_in["total_assets"].iloc[-1] if not hist_all_in.empty else 100000
    final_equity_fixed = hist_fixed["total_assets"].iloc[-1] if not hist_fixed.empty else 100000

    print(f"{'Final Equity':<30} {final_equity_all_in:>18,.2f} {final_equity_fixed:>18,.2f}")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 7. Summary interpretation
    # -------------------------------------------------------------------------
    print("\n### Summary ###")
    print(f"- All-In mode invests nearly all cash on each buy signal.")
    print(f"- Fixed-Fraction mode keeps at least 40% of initial capital (¥40,000) as cash reserve.")
    print(f"- This means Fixed-Fraction trades smaller positions but has lower drawdown risk.")
    print()


if __name__ == "__main__":
    main()
