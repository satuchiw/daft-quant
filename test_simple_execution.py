"""
Simple test to verify next-bar execution timing
"""
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from backtest.engine import Backtester
from strategy.base_strategy import BaseStrategy

class SignalOnDayOneStrategy(BaseStrategy):
    """Strategy that only generates ONE buy signal on first day"""
    def __init__(self):
        super().__init__()
        self.bar_count = 0
    
    def on_init(self):
        self.bar_count = 0
        print("Strategy initialized")
    
    def on_bar(self, bar):
        self.bar_count += 1
        close = bar['close']
        dt = bar['datetime']
        
        print(f"Bar {self.bar_count}: Date={dt.date()}, Close={close:.2f}, Open={bar['open']:.2f}")
        
        # Generate buy signal ONLY on first bar
        if self.bar_count == 1:
            print(f"  → BUY SIGNAL generated (bar closes at {close:.2f})")
            return "buy"
        
        # Generate sell signal ONLY on fourth bar
        if self.bar_count == 4:
            print(f"  → SELL SIGNAL generated (bar closes at {close:.2f})")
            return "sell"
            
        return "hold"
    
    def on_stop(self):
        print("Strategy stopped")

def main():
    print("=" * 70)
    print("SIMPLE EXECUTION TIMING TEST")
    print("=" * 70)
    
    # Create 5 days of data with clear prices
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    
    df = pd.DataFrame({
        'open':  [100.0, 102.0, 104.0, 106.0, 108.0],
        'high':  [101.0, 103.0, 105.0, 107.0, 109.0],
        'low':   [99.0,  101.0, 103.0, 105.0, 107.0],
        'close': [100.5, 102.5, 104.5, 106.5, 108.5],
        'volume': [10000] * 5
    }, index=dates)
    
    print("\nPrice Data:")
    print(df[['open', 'close']])
    print()
    
    # Run backtest
    strategy = SignalOnDayOneStrategy()
    backtester = Backtester(
        data=df,
        strategy=strategy,
        initial_capital=10000,
        commission_rate=0.0,
        stamp_duty=0.0,
        slippage=0.0
    )
    
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST...")
    print("=" * 70 + "\n")
    
    backtester.run()
    
    print("\n" + "=" * 70)
    print("TRADE EXECUTION RESULTS")
    print("=" * 70)
    
    if backtester.trades:
        for i, trade in enumerate(backtester.trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Type: {trade['type'].upper()}")
            print(f"  Date: {trade['datetime'].date()}")
            print(f"  Price: {trade['price']:.2f}")
            print(f"  Quantity: {trade['quantity']}")
    
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    expected_results = [
        {
            'type': 'buy',
            'signal_date': '2024-01-01',
            'exec_date': '2024-01-02',
            'exec_price': 102.0,
            'reason': 'BUY signal on Day 1 should execute at Day 2 open'
        },
        {
            'type': 'sell',
            'signal_date': '2024-01-04',
            'exec_date': '2024-01-05',
            'exec_price': 108.0,
            'reason': 'SELL signal on Day 4 should execute at Day 5 open'
        }
    ]
    
    all_correct = True
    
    for i, (expected, actual) in enumerate(zip(expected_results, backtester.trades), 1):
        print(f"\nTrade {i} Check:")
        print(f"  Expected: {expected['type'].upper()} on {expected['exec_date']} at {expected['exec_price']:.2f}")
        print(f"  Actual:   {actual['type'].upper()} on {actual['datetime'].date()} at {actual['price']:.2f}")
        
        date_match = str(actual['datetime'].date()) == expected['exec_date']
        price_match = abs(actual['price'] - expected['exec_price']) < 0.01
        type_match = actual['type'] == expected['type']
        
        if date_match and price_match and type_match:
            print(f"  ✓ PASS - {expected['reason']}")
        else:
            print(f"  ✗ FAIL - {expected['reason']}")
            all_correct = False
    
    print("\n" + "=" * 70)
    if all_correct:
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("Trades execute at NEXT bar's open (Look-ahead bias FIXED)")
    else:
        print("✗✗✗ TESTS FAILED ✗✗✗")
    print("=" * 70)

if __name__ == "__main__":
    main()
