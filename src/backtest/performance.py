import pandas as pd
import numpy as np
from typing import Dict, Any

class PerformanceAnalyzer:
    """
    Calculates performance metrics for the trading strategy.
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(self, equity_curve: pd.Series, trades: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate key performance metrics.
        
        Args:
            equity_curve (pd.Series): Series of total equity indexed by datetime.
            trades (pd.DataFrame): DataFrame of trades with columns ['entry_price', 'exit_price', 'pnl', ...].
            
        Returns:
            Dict[str, Any]: Dictionary containing performance metrics.
        """
        if equity_curve.empty:
            return {}

        initial_capital = equity_curve.iloc[0]
        final_capital = equity_curve.iloc[-1]
        
        # Returns
        returns = equity_curve.pct_change().dropna()
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Annualized metrics (assuming 252 trading days)
        annualized_return = (1 + total_return) ** (252 / len(equity_curve)) - 1 if len(equity_curve) > 0 else 0
        annualized_volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0
        
        # Sharpe Ratio
        sharpe_ratio = 0.0
        if annualized_volatility != 0:
            sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility
            
        # Max Drawdown
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Trade Statistics
        num_trades = len(trades)
        win_rate = 0.0
        avg_win = 0.0
        avg_loss = 0.0
        profit_factor = 0.0
        
        if num_trades > 0 and 'pnl' in trades.columns:
            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] <= 0]
            
            win_rate = len(winning_trades) / num_trades
            avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0.0
            avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0.0
            
            total_loss = abs(losing_trades['pnl'].sum())
            if total_loss > 0:
                profit_factor = winning_trades['pnl'].sum() / total_loss
            else:
                profit_factor = float('inf') if winning_trades['pnl'].sum() > 0 else 0.0

        return {
            "Initial Capital": initial_capital,
            "Final Capital": final_capital,
            "Total Return": f"{total_return:.2%}",
            "Annualized Return": f"{annualized_return:.2%}",
            "Max Drawdown": f"{max_drawdown:.2%}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Number of Trades": num_trades,
            "Win Rate": f"{win_rate:.2%}",
            "Avg Win": f"{avg_win:.2f}",
            "Avg Loss": f"{avg_loss:.2f}",
            "Profit Factor": f"{profit_factor:.2f}"
        }
