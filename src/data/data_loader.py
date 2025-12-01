import sys
import os
import pandas as pd
from datetime import datetime

# Add Mini-QMT python path
QMT_PYTHON_PATH = r"C:\国金QMT交易端模拟\bin.x64\Lib\site-packages"
if QMT_PYTHON_PATH not in sys.path:
    sys.path.append(QMT_PYTHON_PATH)

try:
    from xtquant import xtdata
except ImportError:
    print(f"Error: Could not import 'xtquant'. Please ensure it exists at {QMT_PYTHON_PATH}")
    raise

class DataManager:
    def __init__(self, storage_path="storage/data"):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def _get_file_path(self, symbol, period, start_time, end_time):
        """
        Generate a unique filename for the requested data.
        """
        # Sanitize symbol (e.g., 000001.SZ -> 000001_SZ)
        safe_symbol = symbol.replace('.', '_')
        # Sanitize dates (remove chars that might be issues in filenames)
        safe_start = start_time.replace('-', '').replace(':', '').replace(' ', '')
        safe_end = end_time.replace('-', '').replace(':', '').replace(' ', '')
        
        filename = f"{safe_symbol}_{period}_{safe_start}_{safe_end}.csv"
        return os.path.join(self.storage_path, filename)

    def fetch_data(self, symbol, period, start_time, end_time):
        """
        Fetch market data.
        1. Check local CSV storage.
        2. If missing, download via Mini-QMT and save.
        
        :param symbol: Stock code (e.g., '000001.SZ')
        :param period: Time scale ('1m', '5m', '1d', etc.)
        :param start_time: Start date/time (e.g., '20230101' or '2023-01-01')
        :param end_time: End date/time (e.g., '20231231')
        :return: pandas DataFrame
        """
        # Normalize time format for filename consistency if needed, 
        # but xtdata accepts various formats. We'll use the input for filename generation.
        file_path = self._get_file_path(symbol, period, start_time, end_time)

        # 1. Check Local Storage
        if os.path.exists(file_path):
            print(f"[DataManager] Loading cached data: {file_path}")
            df = pd.read_csv(file_path)
            # Set index to 'time' or 'date' if present
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
            return df

        # 2. Download from Mini-QMT
        print(f"[DataManager] Downloading from Mini-QMT: {symbol} ({period})")
        
        # Ensure data is downloaded to Mini-QMT's local cache
        # incrementally=True is good practice
        xtdata.download_history_data(symbol, period=period, start_time=start_time, end_time=end_time, incrementally=True)

        # Read from Mini-QMT
        # get_market_data_ex returns a dict {stock_code: dataframe} or just dataframe depending on usage
        # here we ask for specific stock list
        data_dict = xtdata.get_market_data_ex(
            field_list=[], # Empty list means all fields
            stock_list=[symbol], 
            period=period, 
            start_time=start_time, 
            end_time=end_time,
            count=-1,
            dividend_type='none', 
            fill_data=True
        )

        if symbol not in data_dict or data_dict[symbol].empty:
            print(f"[DataManager] Warning: No data found for {symbol}")
            return pd.DataFrame()

        df = data_dict[symbol]
        
        # xtdata returns DataFrame with index as datetime usually (for 1d might be str/int, let's check)
        # For 1d, index is usually YYYYMMDD int or str. For intraday, it is YYYYMMDDHHMMSS int.
        # We convert index to datetime for consistency and saving.
        
        # Check index type
        if not isinstance(df.index, pd.DatetimeIndex):
            # Try to convert index to datetime
            # If index is string or int YYYYMMDD
            try:
                df.index = pd.to_datetime(df.index.astype(str), format='%Y%m%d')
            except:
                # Fallback for intraday which might be YYYYMMDDHHMMSS
                try:
                    df.index = pd.to_datetime(df.index.astype(str), format='%Y%m%d%H%M%S')
                except:
                    pass # Leave as is if fails
        
        df.index.name = 'time'
        
        # 3. Save to Local Storage
        print(f"[DataManager] Saving to {file_path}")
        df.to_csv(file_path)

        return df
