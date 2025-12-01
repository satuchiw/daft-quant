import sys
import os
import pandas as pd

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from backtest.runner import BacktestRunner
from strategy.ma_crossover import MACrossoverStrategy
from backtest.plotting import plot_backtest_results

def main():
    print("Initializing Analysis...")
    
    # Configuration
    # We use a ticker that we know exists in local storage for demonstration
    tickers = ['159919.SZ'] 
    start_date = '20220101'
    end_date = '20231231'
    
    # Strategy Parameters
    strategy_params = {
        'short_window': 10,
        'long_window': 30
    }
    
    # Initialize Runner
    # Default storage path is 'storage/data' relative to CWD
    runner = BacktestRunner()
    
    # Run Batch Backtest
    print(f"Running backtest for {tickers}...")
    results = runner.run_batch(
        tickers=tickers,
        strategy_cls=MACrossoverStrategy,
        strategy_params=strategy_params,
        start_date=start_date,
        end_date=end_date,
        period='1d',
        initial_capital=100000.0
    )
    
    # Display Summary
    print("\n=== Backtest Summary ===")
    if not results['summary'].empty:
        print(results['summary'].to_string())
        
        # Save to CSV
        results['summary'].to_csv('backtest_summary.csv', index=False)
        print("\nSummary saved to backtest_summary.csv")
        
        # Plot Results for each ticker (Optional: limit to first few)
        print("\nPlotting Results...")
        for res in results['details']:
            ticker = res['ticker']
            print(f"Plotting {ticker}...")
            plot_backtest_results(res['history'], res['trades'])
    else:
        print("No results generated.")

if __name__ == "__main__":
    main()
