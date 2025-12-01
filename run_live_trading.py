import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from live_trading.engine import LiveTradeEngine
from strategy.ma_crossover import MACrossoverStrategy

def main():
    # Configuration
    # NOTE: Update this path to your actual Mini-QMT userdata path
    # Usually: C:\国金QMT交易端模拟\userdata_mini
    MINI_QMT_PATH = r"C:\国金QMT交易端模拟\userdata_mini"
    ACCOUNT_ID = "YOUR_ACCOUNT_ID" # Replace with real account ID
    
    SYMBOLS = ['000001.SZ', '600519.SH']
    
    print("--- Live Trading Demo ---")
    print(f"Target Account: {ACCOUNT_ID}")
    print(f"Monitoring: {SYMBOLS}")
    
    # 1. Initialize Strategy
    # We use the same strategy class as backtest!
    strategy = MACrossoverStrategy(short_window=5, long_window=20)
    
    # 2. Initialize Engine
    engine = LiveTradeEngine(
        strategy=strategy,
        account_id=ACCOUNT_ID,
        mini_qmt_path=MINI_QMT_PATH,
        symbols=SYMBOLS,
        period='1d'
    )
    
    # 3. Start
    try:
        # This will block until interrupted
        # Note: Connect will fail if QMT is not running or path is wrong, but we catch it inside or let it crash for demo
        engine.start()
    except Exception as e:
        print(f"Error: {e}")
        print("Ensure Mini-QMT is running and ACCOUNT_ID is correct.")

if __name__ == "__main__":
    main()
