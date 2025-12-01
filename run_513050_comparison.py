"""
Compare RSI strategy on 513050.SH (China Internet ETF)
All-In vs Fixed-Fraction (40% cash reserve)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
from data import DataManager
from strategy.rsi_strategy import RSIStrategy
from backtest.engine import Backtester
from risk.position_sizer import PositionSizingConfig


def run_backtest(data, sizing_config, label):
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
    print(f"\n{'='*60}\nRunning: {label}\n{'='*60}")
    backtester.run()
    return backtester.get_results()


def main():
    dm = DataManager()
    symbol = "513050.SH"
    
    print(f"Fetching data for {symbol}...")
    data = dm.fetch_data(symbol, period="1d", start_time="20100101", end_time="20201231")
    
    if data is None or data.empty:
        print("ERROR: No data available")
        return
    
    print(f"Data: {len(data)} bars from {data.index[0].date()} to {data.index[-1].date()}")
    
    # Configs
    config_all_in = PositionSizingConfig(method="all_in")
    config_fixed = PositionSizingConfig(method="fixed_fraction", fraction=1.0, min_cash_fraction=0.4)
    
    # Run
    r1 = run_backtest(data, config_all_in, "All-In")
    r2 = run_backtest(data, config_fixed, "Fixed-Fraction (40% reserve)")
    
    # Compare
    m1, m2 = r1["metrics"], r2["metrics"]
    h1, h2 = r1["history"], r2["history"]
    
    print("\n" + "="*70)
    print(f"COMPARISON: 513050.SH (China Internet ETF) - RSI Strategy")
    print("="*70)
    print(f"{'Metric':<30} {'All-In':>18} {'Fixed-Fraction':>18}")
    print("-"*70)
    
    for key in sorted(set(m1.keys()) | set(m2.keys())):
        v1, v2 = m1.get(key, "N/A"), m2.get(key, "N/A")
        fmt = lambda v: f"{v:.4f}" if isinstance(v, float) else str(v)
        print(f"{key:<30} {fmt(v1):>18} {fmt(v2):>18}")
    
    print("-"*70)
    print(f"{'Closed Trades':<30} {len(r1['trades']):>18} {len(r2['trades']):>18}")
    
    eq1 = h1["total_assets"].iloc[-1] if not h1.empty else 100000
    eq2 = h2["total_assets"].iloc[-1] if not h2.empty else 100000
    print(f"{'Final Equity':<30} {eq1:>18,.2f} {eq2:>18,.2f}")
    print("="*70)


if __name__ == "__main__":
    main()
