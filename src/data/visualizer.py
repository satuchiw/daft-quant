import mplfinance as mpf
import pandas as pd

def plot_kline(df, title="Stock Price"):
    """
    Plot K-line chart using mplfinance.
    
    :param df: pandas DataFrame with 'open', 'high', 'low', 'close', 'volume' columns.
               Index should be datetime.
    :param title: Chart title
    """
    if df.empty:
        print("No data to plot.")
        return

    # Prepare DataFrame for mplfinance
    plot_data = df.copy()
    
    # Ensure index is datetime
    if not isinstance(plot_data.index, pd.DatetimeIndex):
        # Try to convert 'time' or 'date' column to index if index is not datetime
        if 'time' in plot_data.columns:
             plot_data['time'] = pd.to_datetime(plot_data['time'])
             plot_data.set_index('time', inplace=True)
        elif 'date' in plot_data.columns:
             plot_data['date'] = pd.to_datetime(plot_data['date'])
             plot_data.set_index('date', inplace=True)
        else:
            # Try parsing the index itself
             plot_data.index = pd.to_datetime(plot_data.index)

    # Ensure columns are float
    cols = ['open', 'high', 'low', 'close', 'volume']
    for col in cols:
        if col in plot_data.columns:
            plot_data[col] = plot_data[col].astype(float)
        else:
            print(f"Warning: Missing column {col} for plotting")

    # Create style
    mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc)

    # Plot
    try:
        mpf.plot(plot_data, type='candle', style=s, title=title, volume=True)
    except Exception as e:
        print(f"Error plotting data: {e}")
