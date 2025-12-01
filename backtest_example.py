import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from backtest.engine import Backtester
from strategy.ma_crossover import MACrossoverStrategy
from backtest.plotting import plot_backtest_results

def generate_dummy_data(days=200):
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    # Generate random walk
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, days)
    price_path = 100 * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        'open': price_path,
        'high': price_path * 1.01,
        'low': price_path * 0.99,
        'close': price_path,
        'volume': np.random.randint(1000, 10000, days)
    }, index=dates)
    
    return df

def main():
    print("Generating dummy data...")
    df = generate_dummy_data(300)
    
    print("Initializing Strategy...")
    # Short window 10, Long window 30
    strategy = MACrossoverStrategy(short_window=10, long_window=30)
    
    print("Initializing Backtester...")
    backtester = Backtester(
        data=df,
        strategy=strategy,
        initial_capital=100000.0,
        commission_rate=0.0003,
        stamp_duty=0.001
    )
    
    print("Running Backtest...")
    backtester.run()
    
    print("Analyzing Results...")
    results = backtester.get_results()
    
    metrics = results['metrics']
    print("\nPerformance Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v}")
        
    # Verify trades were made
    print(f"\nTotal Closed Trades: {len(results['trades'])}")
    if not results['trades'].empty:
        print(results['trades'].head())
        
    # Plotting (Commented out to avoid GUI requirement in headless env, but code is valid)
    # print("Plotting results...")
    # plot_backtest_results(results['history'], results['trades'])

if __name__ == "__main__":
    main()
