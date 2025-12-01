import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

from strategy.base_strategy import BaseStrategy
from .performance import PerformanceAnalyzer
from risk.position_sizer import PositionSizer, PositionSizingConfig

class Backtester:
    """
    Event-driven backtesting engine.
    """
    
    def __init__(
        self, 
        data: pd.DataFrame, 
        strategy: BaseStrategy, 
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        stamp_duty: float = 0.001, # Only on sell
        slippage: float = 0.0,
        sizing_config: Optional[PositionSizingConfig] = None,
    ):
        """
        Initialize the backtester.
        
        Args:
            data: DataFrame with datetime index and columns: open, high, low, close, volume
            strategy: Instance of a class inheriting BaseStrategy
            initial_capital: Starting cash
            commission_rate: Commission rate per trade (e.g., 0.0003 for 0.03%)
            stamp_duty: Tax on selling (e.g. 0.001 for 0.1%)
            slippage: Estimated slippage ratio
        """
        self.data = data.copy()
        # Ensure index is datetime
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(self.data.index)
        self.data.sort_index(inplace=True)
        
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.stamp_duty = stamp_duty
        self.slippage = slippage
        
        # Position sizing helper
        # Default: legacy all-in behavior; users can pass a different config
        self.position_sizer = PositionSizer(
            config=sizing_config or PositionSizingConfig(method="all_in"),
            initial_capital=self.initial_capital,
        )

        # State
        self.cash = initial_capital
        self.position = 0 # Quantity of shares
        self.frozen_position = 0 # Shares bought today (T+1 rule)
        self.last_date = None
        self.avg_cost = 0.0
        
        # Pending signal (to be executed at next bar's open)
        self.pending_signal = None
        self.pending_signal_data = None
        
        # History
        self.history: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = [] # Executions
        self.closed_trades: List[Dict[str, Any]] = [] # Paired trades for PnL
        
    def run(self):
        """
        Run the backtest simulation.
        Trades are executed at next bar's open to avoid look-ahead bias.
        """
        print(f"Starting backtest from {self.data.index[0]} to {self.data.index[-1]}")
        self.strategy.on_init()
        
        for i in range(len(self.data)):
            # Prepare bar data
            index = self.data.index[i]
            
            # T+1 Logic: Unlock frozen shares if date has changed
            current_date = index.date()
            if self.last_date is None:
                self.last_date = current_date
            elif current_date > self.last_date:
                self.frozen_position = 0
                self.last_date = current_date
            
            row = self.data.iloc[i]
            
            bar = {
                'datetime': index,
                'open': row.get('open'),
                'high': row.get('high'),
                'low': row.get('low'),
                'close': row.get('close'),
                'volume': row.get('volume', 0)
            }
            
            # Execute pending signal from previous bar at current bar's OPEN
            if self.pending_signal is not None:
                exec_price = bar['open']
                exec_date = index
                
                if self.pending_signal == "buy":
                    qty = None
                    cash_amount = None
                    if isinstance(self.pending_signal_data, dict):
                        qty = self.pending_signal_data.get('quantity')
                        cash_amount = self.pending_signal_data.get('cash_amount')
                    self._buy(exec_price, exec_date, qty, cash_amount)
                elif self.pending_signal == "sell":
                    qty = self.pending_signal_data.get('quantity') if isinstance(self.pending_signal_data, dict) else None
                    self._sell(exec_price, exec_date, qty)
                
                # Clear pending signal
                self.pending_signal = None
                self.pending_signal_data = None
            
            # Generate signal from strategy based on current bar
            signal = self.strategy.on_bar(bar)
            
            # Store signal to be executed at NEXT bar's open (avoid look-ahead bias)
            if signal == "buy" or signal == "sell":
                self.pending_signal = signal
                self.pending_signal_data = None
            elif isinstance(signal, dict):
                # Handle custom signal dict
                action = signal.get('action')
                if action == "buy" or action == "sell":
                    self.pending_signal = action
                    self.pending_signal_data = signal
            else:
                # "hold" or other signals - clear pending
                self.pending_signal = None
                self.pending_signal_data = None
            
            # Update portfolio history using current bar's close price for valuation
            current_price = bar['close']
            portfolio_value = self.cash + (self.position * current_price)
            self.history.append({
                'datetime': index,
                'cash': self.cash,
                'position': self.position,
                'close': current_price,
                'total_assets': portfolio_value
            })
            
        self.strategy.on_stop()
        print("Backtest completed.")
        
    def _buy(self, price: float, date: datetime, quantity: Optional[int] = None, cash_amount: Optional[float] = None):
        # Apply slippage
        exec_price = price * (1 + self.slippage)
        
        # If cash_amount specified (e.g., DCA strategy), calculate quantity from it
        if cash_amount is not None:
            if self.cash <= 0:
                return
            # Use the lesser of specified cash_amount or available cash
            available = min(cash_amount, self.cash * 0.99)
            max_qty = int(available / exec_price)
            quantity = (max_qty // 100) * 100  # Round to lot size
        # If quantity not specified, delegate to PositionSizer
        elif quantity is None:
            if self.cash <= 0:
                return
            quantity = self.position_sizer.size(
                price=exec_price,
                cash_available=self.cash,
                current_position=self.position,
            )
            
        if quantity <= 0:
            return

        cost = quantity * exec_price
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        if self.cash >= total_cost:
            # Update Average Cost
            # new_avg = (old_qty * old_avg + new_qty * new_price) / total_qty
            prev_val = self.position * self.avg_cost
            new_val = quantity * exec_price # Use raw price or exec price for cost basis? usually exec
            
            self.cash -= total_cost
            self.position += quantity
            self.frozen_position += quantity
            self.avg_cost = (prev_val + new_val) / self.position
            
            self.trades.append({
                'datetime': date,
                'type': 'buy',
                'price': exec_price,
                'quantity': quantity,
                'commission': commission
            })
            
    def _sell(self, price: float, date: datetime, quantity: Optional[int] = None):
        tradeable_position = self.position - self.frozen_position
        if tradeable_position <= 0:
            return
            
        exec_price = price * (1 - self.slippage)
        
        if quantity is None:
            quantity = tradeable_position
            
        if quantity > tradeable_position:
            quantity = tradeable_position
            
        # Must sell in lots of 100? Usually yes, but let's be flexible here.
        
        revenue = quantity * exec_price
        commission = revenue * self.commission_rate
        tax = revenue * self.stamp_duty
        total_revenue = revenue - commission - tax
        
        # Calculate PnL for this trade
        # FIFO or Average Cost? Using Average Cost
        trade_pnl = (exec_price - self.avg_cost) * quantity - commission - tax
        
        entry_avg_cost = self.avg_cost

        self.cash += total_revenue
        self.position -= quantity
        
        if self.position == 0:
            self.avg_cost = 0.0
            
        self.trades.append({
            'datetime': date,
            'type': 'sell',
            'price': exec_price,
            'quantity': quantity,
            'commission': commission + tax
        })
        
        self.closed_trades.append({
            'datetime': date,
            'entry_price': entry_avg_cost, 
            'exit_price': exec_price,
            'quantity': quantity,
            'pnl': trade_pnl,
            'return_pct': (trade_pnl / (entry_avg_cost * quantity)) if entry_avg_cost > 0 else 0
        })

    def get_results(self) -> Dict[str, Any]:
        """
        Return backtest results including metrics and dataframes.
        """
        df_history = pd.DataFrame(self.history)
        if not df_history.empty:
            df_history.set_index('datetime', inplace=True)
            
        df_trades = pd.DataFrame(self.closed_trades)
        
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.calculate_metrics(df_history['total_assets'] if not df_history.empty else pd.Series(), df_trades)
        
        return {
            'metrics': metrics,
            'history': df_history,
            'trades': df_trades,
            'all_trades': self.trades  # All buy/sell executions for charting
        }
