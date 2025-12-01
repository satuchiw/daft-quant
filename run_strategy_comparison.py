"""
Compare 3 strategies on 510050.SH (SSE 50 ETF) 2010-2020:
1. RSI All-In
2. RSI Fixed-Fraction (40% cash reserve)
3. Weekly DCA (Dollar Cost Averaging)

Initial Capital: 100,000
DCA: Splits 100,000 evenly across ~520 weeks (2010-2020)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data import DataManager
from strategy.rsi_strategy import RSIStrategy
from strategy.dca_strategy import DCAStrategy
from backtest.engine import Backtester
from risk.position_sizer import PositionSizingConfig


def run_comparison(symbol: str, start: str, end: str):
    dm = DataManager()
    
    print(f"\nFetching data for {symbol} ({start[:4]}-{end[:4]})...")
    data = dm.fetch_data(symbol, period="1d", start_time=start, end_time=end)
    
    if data is None or data.empty:
        print("ERROR: No data")
        return
    
    print(f"Data: {len(data)} bars from {data.index[0].date()} to {data.index[-1].date()}")
    
    # Calculate weeks in data for DCA
    weeks = len(data) / 5  # ~5 trading days per week
    weekly_amount = 100000 / weeks  # Split initial capital across all weeks
    print(f"DCA: ~{weeks:.0f} weeks, investing ~{weekly_amount:.2f}/week")
    
    results = {}
    
    # 1. RSI All-In
    print("\n" + "="*60 + "\n1. RSI All-In\n" + "="*60)
    s1 = RSIStrategy(period=14, overbought=70, oversold=30)
    bt1 = Backtester(data, s1, initial_capital=100000, sizing_config=PositionSizingConfig(method="all_in"))
    bt1.run()
    results["RSI All-In"] = bt1.get_results()
    
    # 2. RSI Fixed-Fraction
    print("\n" + "="*60 + "\n2. RSI Fixed-Fraction (40% reserve)\n" + "="*60)
    s2 = RSIStrategy(period=14, overbought=70, oversold=30)
    bt2 = Backtester(data, s2, initial_capital=100000, sizing_config=PositionSizingConfig(method="fixed_fraction", fraction=1.0, min_cash_fraction=0.4))
    bt2.run()
    results["RSI Fixed"] = bt2.get_results()
    
    # 3. Weekly DCA
    print("\n" + "="*60 + "\n3. Weekly DCA\n" + "="*60)
    s3 = DCAStrategy(weekly_amount=weekly_amount)
    bt3 = Backtester(data, s3, initial_capital=100000)
    bt3.run()
    results["Weekly DCA"] = bt3.get_results()
    
    # Compare
    print("\n" + "="*80)
    print(f"COMPARISON: {symbol} ({start[:4]}-{end[:4]})")
    print("="*80)
    print(f"{'Metric':<24} {'RSI All-In':>18} {'RSI Fixed':>18} {'Weekly DCA':>18}")
    print("-"*80)
    
    metrics_keys = ["Total Return", "Annualized Return", "Max Drawdown", "Sharpe Ratio", "Win Rate", "Number of Trades"]
    
    for k in metrics_keys:
        vals = []
        for name in ["RSI All-In", "RSI Fixed", "Weekly DCA"]:
            v = results[name]["metrics"].get(k, "N/A")
            vals.append(str(v) if v != "N/A" else "N/A")
        print(f"{k:<24} {vals[0]:>18} {vals[1]:>18} {vals[2]:>18}")
    
    print("-"*80)
    
    # Final equity
    for name in ["RSI All-In", "RSI Fixed", "Weekly DCA"]:
        h = results[name]["history"]
        eq = h["total_assets"].iloc[-1] if not h.empty else 100000
        results[name]["final_equity"] = eq
    
    print(f"{'Final Equity':<24} {results['RSI All-In']['final_equity']:>18,.2f} {results['RSI Fixed']['final_equity']:>18,.2f} {results['Weekly DCA']['final_equity']:>18,.2f}")
    print(f"{'Closed Trades':<24} {len(results['RSI All-In']['trades']):>18} {len(results['RSI Fixed']['trades']):>18} {len(results['Weekly DCA']['trades']):>18}")
    print("="*80)
    
    return results


def main():
    print("="*80)
    print("STRATEGY COMPARISON: RSI vs DCA")
    print("="*80)
    
    # 510050.SH (SSE 50 ETF) - has data from 2010
    run_comparison("510050.SH", "20100101", "20201231")
    
    # 510300.SH (CSI 300 ETF) - has data from 2012
    run_comparison("510300.SH", "20100101", "20201231")
    
    print("\n### Summary ###")
    print("- RSI All-In: Aggressive, high return potential but high drawdown risk")
    print("- RSI Fixed: Moderate, reduced drawdown with 40% cash reserve")
    print("- Weekly DCA: Passive, steady accumulation regardless of market timing")
    print()


if __name__ == "__main__":
    main()
