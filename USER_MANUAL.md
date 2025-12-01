# Real Quant User Manual

This manual guides you through using the `real quant` system for backtesting trading strategies and running live trades.

---

## 1. Running a Backtest

Backtesting allows you to simulate how a strategy would have performed in the past.

### Step 1: Configure Parameters
Open the file `run_analysis.py` in your editor. Locate the `main()` function. You will see a section for **Configuration**:

```python
def main():
    # ...
    # 1. Select Tickers
    tickers = ['000001.SZ', '600519.SH'] # Add your stock codes here
    
    # 2. Set Date Range
    start_date = '20220101'
    end_date = '20231231'
    
    # 3. Configure Strategy Parameters
    strategy_params = {
        'short_window': 10, # Short moving average window
        'long_window': 30   # Long moving average window
    }
    # ...
```
- **Tickers**: Update the list with the stock codes you want to test (e.g., `['159915.SZ']`).
- **Date Range**: Set the start and end dates in `YYYYMMDD` format.
- **Strategy Params**: Adjust the strategy-specific settings (like MA windows).

### Step 2: Run the Analysis
Open your terminal or command prompt in the project folder and run:

```bash
python run_analysis.py
```

### Step 3: View Results
1. **Console Output**: You will see a progress log and a final summary table printed in the terminal.
2. **CSV Report**: A detailed summary is saved to `backtest_summary.csv`. You can open this in Excel.
3. **Charts**: The system will pop up a performance chart for each ticker, showing the price history, buy/sell points, and portfolio value.

---

## 2. Creating Your Own Trading Strategy

You can create custom strategies by writing a Python class. All strategies must inherit from `BaseStrategy` and implement three required methods.

### Step 1: Create a New Strategy File

Navigate to the `src/strategy/` folder and create a new Python file. For example, `my_strategy.py`.

### Step 2: Import and Inherit from BaseStrategy

Every strategy must inherit from `BaseStrategy`. Here's the basic template:

```python
from typing import Dict, Any, Union
from .base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, param1=10, param2=20):
        """
        Initialize your strategy with custom parameters.
        """
        super().__init__()
        self.param1 = param1
        self.param2 = param2
        # Add any internal state variables you need
        self.price_history = []
    
    def on_init(self) -> None:
        """
        Called once when the strategy starts.
        Use this to reset state or print initialization info.
        """
        print(f"Initializing MyCustomStrategy with param1={self.param1}")
        self.price_history = []
    
    def on_bar(self, bar: Dict[str, Any]) -> str:
        """
        Called on every new price bar (candle).
        This is where your trading logic goes.
        
        Args:
            bar: Dictionary with keys like:
                - 'datetime': timestamp
                - 'open': opening price
                - 'high': highest price
                - 'low': lowest price
                - 'close': closing price
                - 'volume': trading volume
        
        Returns:
            One of: "buy", "sell", or "hold"
        """
        close = bar.get('close')
        
        if close is None:
            return "hold"
        
        # YOUR LOGIC HERE
        # Example: Buy if price is below a threshold
        if close < 100:
            return "buy"
        elif close > 150:
            return "sell"
        
        return "hold"
    
    def on_stop(self) -> None:
        """
        Called when the strategy stops.
        Use this for cleanup or final logging.
        """
        print("Stopping MyCustomStrategy")
```

### Step 3: Implement Your Trading Logic

The `on_bar()` method is the heart of your strategy. You receive market data and must return a signal.

**Example 1: Simple Price Threshold Strategy**
```python
def on_bar(self, bar: Dict[str, Any]) -> str:
    close = bar['close']
    
    # Buy when price drops below 95
    if close < 95:
        return "buy"
    # Sell when price rises above 105
    elif close > 105:
        return "sell"
    
    return "hold"
```

**Example 2: Bollinger Bands Strategy**
```python
class BollingerBandsStrategy(BaseStrategy):
    def __init__(self, window=20, num_std=2):
        super().__init__()
        self.window = window
        self.num_std = num_std
        self.prices = []
    
    def on_init(self):
        self.prices = []
    
    def on_bar(self, bar):
        close = bar['close']
        self.prices.append(close)
        
        # Need enough data
        if len(self.prices) < self.window:
            return "hold"
        
        # Calculate mean and standard deviation
        recent = self.prices[-self.window:]
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        std = variance ** 0.5
        
        upper_band = mean + self.num_std * std
        lower_band = mean - self.num_std * std
        
        # Buy at lower band, sell at upper band
        if close < lower_band:
            return "buy"
        elif close > upper_band:
            return "sell"
        
        return "hold"
    
    def on_stop(self):
        print("Bollinger Bands Strategy stopped")
```

### Step 4: Use Your Strategy in Backtesting

Open `run_analysis.py` and update the imports and strategy class:

```python
# At the top of the file, import your new strategy
from strategy.my_strategy import MyCustomStrategy

def main():
    # ...
    
    # Use your custom strategy
    results = runner.run_batch(
        tickers=tickers,
        strategy_cls=MyCustomStrategy,  # <-- Change this
        strategy_params={'param1': 15, 'param2': 25},  # Your parameters
        start_date=start_date,
        end_date=end_date,
        period='1d',
        initial_capital=100000.0
    )
```

Then run:
```bash
python run_analysis.py
```

### Step 5: Use Your Strategy in Live Trading

Similarly, in `run_live_trading.py`:

```python
from strategy.my_strategy import MyCustomStrategy

def main():
    # ...
    strategy = MyCustomStrategy(param1=15, param2=25)
    
    engine = LiveTradeEngine(
        strategy=strategy,
        account_id=ACCOUNT_ID,
        mini_qmt_path=MINI_QMT_PATH,
        symbols=SYMBOLS,
        period='1d'
    )
    
    engine.start()
```

### Tips for Strategy Development

1. **Keep State Minimal**: Only store what you need (e.g., recent prices for indicators).
2. **Handle Missing Data**: Always check if `bar['close']` exists before using it.
3. **Test First**: Always backtest your strategy before running it live.
4. **Start Simple**: Begin with basic logic, then add complexity.
5. **Use Technical Indicators**: You can calculate MA, RSI, MACD, etc. within `on_bar()` using stored price history.

### Important: Trade Execution Timing

**The backtest engine executes trades at the NEXT bar's open price to avoid look-ahead bias:**

```
Day 1 (Close at 3:00 PM):
  - Your strategy sees: close = 100.0
  - Strategy decides: "buy"
  - Signal stored (NOT executed yet)

Day 2 (Open at 9:30 AM):
  - Market opens at: 101.5 (price may gap up/down)
  - Your buy order executes at: 101.5 (next bar's open)
```

This is **realistic** because:
- You can't trade after market closes at 3:00 PM
- Your signal generated at close can only be executed next trading day
- The execution price reflects real market conditions (gaps, slippage)

**Example with your strategy:**
```python
def on_bar(self, bar):
    close = bar['close']  # You see day's close price
    if close < 95:
        return "buy"  # Signal generated, executed TOMORROW at market open
```

---

## 3. Using the Live Trading Interface

The live trading module connects your strategy to the Mini-QMT software to execute real trades.

### Prerequisites
1. **Mini-QMT Software**: You must have the Mini-QMT trading terminal installed and running on your machine.
2. **Account ID**: You need your trading account ID (displayed in QMT).

### Step 1: Configure Live Settings
Open `run_live_trading.py`. Locate the `main()` function and update the following variables:

```python
def main():
    # Path to your Mini-QMT userdata folder
    # Example: C:\国金QMT交易端模拟\userdata_mini
    MINI_QMT_PATH = r"C:\Path\To\Your\userdata_mini"
    
    # Your Account ID (e.g., '8881234567')
    
    ACCOUNT_ID = "YOUR_ACCOUNT_ID" 
    
    # Stocks to monitor and trade
    SYMBOLS = ['000001.SZ', '600519.SH']
```

### Step 2: Start Live Trading
Ensure Mini-QMT is running and you are logged in. Then run:

```bash
python run_live_trading.py
```

### Step 3: Monitoring
- The script will connect to QMT and start monitoring real-time prices.
- **Console Logs**: You will see "Heartbeat" messages or trade signals (`[BUY]`, `[SELL]`) appearing in the console.
- **Execution**: When a signal is triggered, the order is automatically sent to QMT. You can verify the order in the Mini-QMT terminal under the "Orders" tab.

### Safety Notes
- **Demo Mode**: It is highly recommended to use a simulation account first.
- **Monitoring**: Do not leave the script running unattended for long periods without supervision.
