from src.data.data_loader import DataManager
from src.data.visualizer import plot_kline

def main():
    print("Initializing Data Manager...")
    # Initialize Data Manager
    manager = DataManager(storage_path="storage/data")
    
    # Test Parameters
    symbol = "000001.SZ"  # Ping An Bank
    start_date = "20120101"
    end_date = "20231231"
    period = "1d"

    print(f"\n--- Requesting Data: {symbol} ({period}) [{start_date} to {end_date}] ---")
    
    # Fetch Data
    try:
        df = manager.fetch_data(symbol, period, start_date, end_date)
        
        print(f"\nData Retrieved: {len(df)} records")
        if not df.empty:
            print(df.head())
            print(df.tail())
            
            # Visualize
            print("\nVisualizing Data...")
            plot_kline(df, title=f"{symbol} {period}")
        else:
            print("No data found.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
