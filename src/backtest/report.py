"""
Backtest Report Generator
Saves summary text and graphs for each backtest run.
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class BacktestReport:
    """Generate and save backtest reports including text summary and graphs."""
    
    def __init__(self, output_dir: str = "backtest_reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_report(
        self,
        results: Dict[str, Any],
        data: pd.DataFrame,
        strategy_name: str,
        symbol: str,
        sizing_method: str = "default",
        initial_capital: float = 100000.0,
        save: bool = True
    ) -> str:
        """
        Generate a complete backtest report.
        
        Args:
            results: Output from Backtester.get_results()
            data: Original price data DataFrame
            strategy_name: Name of the strategy
            symbol: Stock symbol
            sizing_method: Position sizing method used
            initial_capital: Starting capital
            save: Whether to save files to disk
            
        Returns:
            Path to the report directory
        """
        # Create unique folder for this report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_symbol = symbol.replace(".", "_")
        report_name = f"{safe_symbol}_{strategy_name}_{sizing_method}_{timestamp}"
        report_dir = os.path.join(self.output_dir, report_name)
        
        if save:
            os.makedirs(report_dir, exist_ok=True)
        
        metrics = results.get("metrics", {})
        history = results.get("history", pd.DataFrame())
        trades_df = results.get("trades", pd.DataFrame())
        
        # Get all trades (buy and sell) from backtester
        all_trades = results.get("all_trades", [])
        
        if save:
            # 1. Save text summary
            self._save_summary(report_dir, metrics, strategy_name, symbol, sizing_method, initial_capital, history, trades_df)
            
            # 2. Generate and save graphs
            self._save_equity_curve(report_dir, history, strategy_name, symbol)
            self._save_drawdown_chart(report_dir, history, strategy_name, symbol)
            self._save_price_chart_with_trades(report_dir, data, all_trades, strategy_name, symbol)
            self._save_metrics_summary_chart(report_dir, metrics, strategy_name, symbol)
            
            print(f"Report saved to: {report_dir}")
        
        return report_dir
    
    def _save_summary(
        self,
        report_dir: str,
        metrics: Dict,
        strategy_name: str,
        symbol: str,
        sizing_method: str,
        initial_capital: float,
        history: pd.DataFrame,
        trades_df: pd.DataFrame
    ):
        """Save text summary of backtest results."""
        summary_path = os.path.join(report_dir, "summary.txt")
        
        final_equity = history["total_assets"].iloc[-1] if not history.empty else initial_capital
        start_date = history.index[0] if not history.empty else "N/A"
        end_date = history.index[-1] if not history.empty else "N/A"
        
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("BACKTEST REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("CONFIGURATION\n")
            f.write("-" * 70 + "\n")
            f.write(f"Symbol:           {symbol}\n")
            f.write(f"Strategy:         {strategy_name}\n")
            f.write(f"Position Sizing:  {sizing_method}\n")
            f.write(f"Initial Capital:  {initial_capital:,.2f}\n")
            f.write(f"Period:           {start_date} to {end_date}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 70 + "\n")
            
            for key, value in sorted(metrics.items()):
                if isinstance(value, float):
                    if "Return" in key or "Drawdown" in key or "Rate" in key:
                        f.write(f"{key:<25} {value:>15}\n")
                    else:
                        f.write(f"{key:<25} {value:>15,.4f}\n")
                else:
                    f.write(f"{key:<25} {str(value):>15}\n")
            
            f.write(f"\n{'Final Equity':<25} {final_equity:>15,.2f}\n")
            f.write(f"{'Profit/Loss':<25} {final_equity - initial_capital:>15,.2f}\n")
            
            f.write("\n" + "-" * 70 + "\n")
            f.write("TRADE SUMMARY\n")
            f.write("-" * 70 + "\n")
            
            if not trades_df.empty:
                f.write(f"Total Closed Trades:  {len(trades_df)}\n")
                
                if "pnl" in trades_df.columns:
                    winning = trades_df[trades_df["pnl"] > 0]
                    losing = trades_df[trades_df["pnl"] <= 0]
                    
                    f.write(f"Winning Trades:       {len(winning)}\n")
                    f.write(f"Losing Trades:        {len(losing)}\n")
                    
                    if len(winning) > 0:
                        f.write(f"Avg Win:              {winning['pnl'].mean():,.2f}\n")
                        f.write(f"Largest Win:          {winning['pnl'].max():,.2f}\n")
                    
                    if len(losing) > 0:
                        f.write(f"Avg Loss:             {losing['pnl'].mean():,.2f}\n")
                        f.write(f"Largest Loss:         {losing['pnl'].min():,.2f}\n")
            else:
                f.write("No closed trades.\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 70 + "\n")
    
    def _save_equity_curve(self, report_dir: str, history: pd.DataFrame, strategy_name: str, symbol: str):
        """Save equity curve chart."""
        if history.empty:
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(history.index, history["total_assets"], linewidth=1.5, color="blue", label="Portfolio Value")
        ax.axhline(y=history["total_assets"].iloc[0], color="gray", linestyle="--", alpha=0.7, label="Initial Capital")
        
        ax.set_title(f"Equity Curve - {symbol} ({strategy_name})", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Portfolio Value")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "equity_curve.png"), dpi=150)
        plt.close()
    
    def _save_drawdown_chart(self, report_dir: str, history: pd.DataFrame, strategy_name: str, symbol: str):
        """Save drawdown chart."""
        if history.empty:
            return
        
        # Calculate drawdown
        equity = history["total_assets"]
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max * 100
        
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ax.fill_between(history.index, drawdown, 0, color="red", alpha=0.3)
        ax.plot(history.index, drawdown, color="red", linewidth=1)
        
        ax.set_title(f"Drawdown - {symbol} ({strategy_name})", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Drawdown (%)")
        ax.grid(True, alpha=0.3)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "drawdown.png"), dpi=150)
        plt.close()
    
    def _save_price_chart_with_trades(
        self,
        report_dir: str,
        data: pd.DataFrame,
        all_trades: list,
        strategy_name: str,
        symbol: str
    ):
        """Save price chart with buy/sell markers."""
        if data.empty:
            return
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot price
        ax.plot(data.index, data["close"], linewidth=1, color="black", alpha=0.7, label="Close Price")
        
        # Separate buy and sell trades
        buy_dates = []
        buy_prices = []
        sell_dates = []
        sell_prices = []
        
        for trade in all_trades:
            trade_date = trade.get("datetime")
            trade_price = trade.get("price")
            trade_type = trade.get("type")
            
            if trade_type == "buy":
                buy_dates.append(trade_date)
                buy_prices.append(trade_price)
            elif trade_type == "sell":
                sell_dates.append(trade_date)
                sell_prices.append(trade_price)
        
        # Plot buy markers (green triangles pointing up)
        if buy_dates:
            ax.scatter(buy_dates, buy_prices, marker="^", color="green", s=100, label=f"Buy ({len(buy_dates)})", zorder=5)
        
        # Plot sell markers (red triangles pointing down)
        if sell_dates:
            ax.scatter(sell_dates, sell_prices, marker="v", color="red", s=100, label=f"Sell ({len(sell_dates)})", zorder=5)
        
        ax.set_title(f"Price Chart with Trades - {symbol} ({strategy_name})", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "price_with_trades.png"), dpi=150)
        plt.close()
    
    def _save_metrics_summary_chart(self, report_dir: str, metrics: Dict, strategy_name: str, symbol: str):
        """Save a visual summary of key metrics."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # Extract key metrics
        total_return = metrics.get("Total Return", "0%")
        if isinstance(total_return, str):
            total_return = float(total_return.replace("%", ""))
        
        max_dd = metrics.get("Max Drawdown", "0%")
        if isinstance(max_dd, str):
            max_dd = float(max_dd.replace("%", ""))
        
        sharpe = metrics.get("Sharpe Ratio", 0)
        if isinstance(sharpe, str):
            sharpe = float(sharpe)
        
        win_rate = metrics.get("Win Rate", "0%")
        if isinstance(win_rate, str):
            win_rate = float(win_rate.replace("%", ""))
        
        profit_factor = metrics.get("Profit Factor", 0)
        if isinstance(profit_factor, str):
            profit_factor = float(profit_factor)
        
        num_trades = metrics.get("Number of Trades", 0)
        
        # 1. Return bar
        ax1 = axes[0, 0]
        color = "green" if total_return >= 0 else "red"
        ax1.barh(["Total Return"], [total_return], color=color, height=0.5)
        ax1.axvline(x=0, color="black", linewidth=0.5)
        ax1.set_xlabel("Return (%)")
        ax1.set_title("Total Return")
        ax1.set_xlim(min(-50, total_return - 10), max(50, total_return + 10))
        
        # 2. Drawdown bar
        ax2 = axes[0, 1]
        ax2.barh(["Max Drawdown"], [max_dd], color="red", height=0.5)
        ax2.set_xlabel("Drawdown (%)")
        ax2.set_title("Maximum Drawdown")
        ax2.set_xlim(min(-60, max_dd - 10), 0)
        
        # 3. Win Rate pie
        ax3 = axes[1, 0]
        if win_rate > 0:
            ax3.pie([win_rate, 100 - win_rate], labels=["Win", "Loss"], 
                    colors=["green", "red"], autopct="%1.1f%%", startangle=90)
        else:
            ax3.text(0.5, 0.5, "No Trades", ha="center", va="center", fontsize=14)
        ax3.set_title("Win Rate")
        
        # 4. Key metrics text
        ax4 = axes[1, 1]
        ax4.axis("off")
        metrics_text = f"""
        Key Metrics Summary
        ─────────────────────
        Sharpe Ratio:    {sharpe:.2f}
        Profit Factor:   {profit_factor:.2f}
        Number of Trades: {num_trades}
        Win Rate:        {win_rate:.1f}%
        """
        ax4.text(0.1, 0.5, metrics_text, fontsize=12, family="monospace", va="center")
        
        fig.suptitle(f"Metrics Summary - {symbol} ({strategy_name})", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "metrics_summary.png"), dpi=150)
        plt.close()
