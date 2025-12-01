import pandas as pd
from typing import List, Type, Dict, Any, Optional
import sys
import os
from pathlib import Path

# Add src to path to ensure imports work if this file is imported from elsewhere
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from .engine import Backtester
from strategy.base_strategy import BaseStrategy
from data import DataManager

class BacktestRunner:
    def __init__(self, storage_path: str = "storage/data"):
        self.data_manager = DataManager(storage_path=storage_path)

    def run_batch(
        self,
        tickers: List[str],
        strategy_cls: Type[BaseStrategy],
        strategy_params: Dict[str, Any],
        start_date: str,
        end_date: str,
        period: str = '1d',
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        stamp_duty: float = 0.001
    ) -> Dict[str, Any]:
        """
        Run backtest on a list of tickers.
        
        Args:
            tickers: List of stock codes (e.g. ['000001.SZ', '600000.SH'])
            strategy_cls: The strategy class to use (e.g. MACrossoverStrategy)
            strategy_params: Dictionary of parameters for the strategy
            start_date: Start date 'YYYYMMDD' or 'YYYY-MM-DD'
            end_date: End date
            period: '1d', '1m', etc.
            
        Returns:
            Dict with 'summary' (DataFrame) and 'details' (List)
        """
        results = []
        summary_list = []
        
        print(f"Starting Batch Backtest on {len(tickers)} tickers from {start_date} to {end_date}...")
        
        for ticker in tickers:
            print(f"\n--- Processing {ticker} ---")
            try:
                # 1. Fetch Data
                df = self.data_manager.fetch_data(ticker, period, start_date, end_date)
                
                if df is None or df.empty:
                    print(f"Skipping {ticker}: No data found.")
                    continue
                
                # 2. Initialize Strategy
                strategy = strategy_cls(**strategy_params)
                
                # 3. Run Backtest
                engine = Backtester(
                    data=df,
                    strategy=strategy,
                    initial_capital=initial_capital,
                    commission_rate=commission_rate,
                    stamp_duty=stamp_duty
                )
                engine.run()
                
                # 4. Collect Results
                res = engine.get_results()
                metrics = res['metrics']
                
                if not metrics:
                     print(f"No trades or metrics for {ticker}")
                     # Still add to summary/results with empty metrics?
                     # Better to skip or add basic info
                else:
                    # Add Ticker info
                    metrics['Ticker'] = ticker
                    summary_list.append(metrics)
                
                results.append({
                    'ticker': ticker,
                    'metrics': metrics,
                    'history': res['history'],
                    'trades': res['trades']
                })
                
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                
        # Create Summary DataFrame
        if summary_list:
            summary_df = pd.DataFrame(summary_list)
            # Reorder columns: Ticker first
            cols = ['Ticker'] + [c for c in summary_df.columns if c != 'Ticker']
            summary_df = summary_df[cols]
        else:
            summary_df = pd.DataFrame()
            
        print("\nBatch Backtest Completed.")
        return {
            'summary': summary_df,
            'details': results
        }
