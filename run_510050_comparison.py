"""
Compare RSI strategy on 510050.SH (SSE 50 ETF) 2010-2020
All-In vs Fixed-Fraction (40% cash reserve)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data import DataManager
from strategy.rsi_strategy import RSIStrategy
from backtest.engine import Backtester
from risk.position_sizer import PositionSizingConfig


def main():
    dm = DataManager()
    symbol = "510050.SH"
    
    print(f"Fetching data for {symbol} (2010-2020)...")
    data = dm.fetch_data(symbol, period="1d", start_time="20100101", end_time="20201231")
    
    if data is None or data.empty:
        print("ERROR: No data")
        return
    
    print(f"Data: {len(data)} bars from {data.index[0].date()} to {data.index[-1].date()}")
    
    # All-In
    print("\n" + "="*60 + "\nRunning: All-In\n" + "="*60)
    s1 = RSIStrategy(period=14, overbought=70, oversold=30)
    bt1 = Backtester(data, s1, initial_capital=100000, sizing_config=PositionSizingConfig(method="all_in"))
    bt1.run()
    r1 = bt1.get_results()
    
    # Fixed-Fraction
    print("\n" + "="*60 + "\nRunning: Fixed-Fraction (40% reserve)\n" + "="*60)
    s2 = RSIStrategy(period=14, overbought=70, oversold=30)
    bt2 = Backtester(data, s2, initial_capital=100000, sizing_config=PositionSizingConfig(method="fixed_fraction", fraction=1.0, min_cash_fraction=0.4))
    bt2.run()
    r2 = bt2.get_results()
    
    m1, m2 = r1["metrics"], r2["metrics"]
    h1, h2 = r1["history"], r2["history"]
    
    print("\n" + "="*70)
    print("510050.SH (SSE 50 ETF) RSI Strategy: 2010-2020")
    print("="*70)
    print(f"{'Metric':<28} {'All-In':>20} {'Fixed-Fraction':>20}")
    print("-"*70)
    
    for k in sorted(m1.keys()):
        v1, v2 = m1.get(k, "N/A"), m2.get(k, "N/A")
        print(f"{k:<28} {str(v1):>20} {str(v2):>20}")
    
    print("-"*70)
    eq1 = h1["total_assets"].iloc[-1] if not h1.empty else 100000
    eq2 = h2["total_assets"].iloc[-1] if not h2.empty else 100000
    print(f"{'Final Equity':<28} {eq1:>20,.2f} {eq2:>20,.2f}")
    print(f"{'Closed Trades':<28} {len(r1['trades']):>20} {len(r2['trades']):>20}")
    print("="*70)


if __name__ == "__main__":
    main()
