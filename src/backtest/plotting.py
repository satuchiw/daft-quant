import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

def plot_backtest_results(history: pd.DataFrame, trades: pd.DataFrame, data: pd.DataFrame = None):
    """
    Plot backtest results: Equity Curve and Position/Drawdown.
    Optionally plot Buy/Sell markers on K-line if 'data' is provided.
    """
    if history.empty:
        print("No history to plot.")
        return

    # Setup figure
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])
    
    # 1. Equity Curve
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(history.index, history['total_assets'], label='Equity', color='blue')
    ax1.set_title('Equity Curve')
    ax1.set_ylabel('Value')
    ax1.grid(True)
    
    # 2. Drawdown
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    rolling_max = history['total_assets'].cummax()
    drawdown = (history['total_assets'] - rolling_max) / rolling_max
    ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3, label='Drawdown')
    ax2.set_title('Drawdown')
    ax2.set_ylabel('%')
    ax2.grid(True)
    
    # 3. Positions
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.plot(history.index, history['position'], label='Position (Shares)', color='orange')
    ax3.set_title('Position Size')
    ax3.set_ylabel('Shares')
    ax3.grid(True)
    
    plt.tight_layout()
    plt.show()

def plot_candles_with_trades(data: pd.DataFrame, trades: pd.DataFrame):
    """
    Plot candlestick chart with buy/sell markers.
    """
    if data.empty:
        return
        
    # Prepare markers
    # we need a series with same index as data, containing prices at trade points
    # buys
    buy_trades = trades[trades['pnl'] > 0] # Wait, trades provided here are Closed Trades which only have Exit info usually?
    # Actually the engine returns 'closed_trades' which has entry and exit info but scattered in time?
    # No, 'trades' in engine.get_results() is closed trades.
    # We might need the raw execution log to plot Buy AND Sell points correctly.
    # Let's just use mplfinance addplot if possible, or standard matplotlib.
    
    # Simple approach: just show the provided data using mplfinance
    # Markers would require precise timestamps matching the data index.
    
    # Ensure data has the right columns for mplfinance
    # mpf expects Open, High, Low, Close, Volume
    df = data.copy()
    df.index.name = 'Date'
    
    # Create subplots or add-ons if we had trade points
    # For now, just plot the candles
    mpf.plot(df, type='candle', style='charles', volume=True, title='Price History')
