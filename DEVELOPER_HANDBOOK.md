# Real Quant Developer Handbook

This handbook provides a technical overview of the `real quant` project, detailing the architecture, modules, and file responsibilities. It is intended for developers who want to extend or modify the codebase.

## Project Structure

The project follows a modular architecture, separating data, strategy logic, backtesting core, and live trading execution.

```
real quant/
├── src/
│   ├── backtest/       # Backtesting engine and batch runner
│   ├── data/           # Data acquisition and local caching
│   ├── live_trading/   # Live trading execution engine
│   └── strategy/       # Trading strategy implementations
├── storage/            # Local data storage (CSV files)
├── main.py             # Data fetching demonstration script
├── run_analysis.py     # Main entry point for batch backtesting
├── run_live_trading.py # Main entry point for live trading
└── backtest_example.py # Simple single-ticker backtest example
```

## Modules Detail

### 1. Data Module (`src/data/`)
Responsible for fetching market data from Mini-QMT (`xtquant`) and caching it locally.

- **`data_loader.py`**: 
  - Contains the `DataLoader` class.
  - **Key Methods**:
    - `load_data(ticker, start_date, end_date, period)`: Main interface. Checks local cache first; if missing or incomplete, fetches from QMT and updates cache.
    - `fetch_from_qmt(...)`: Connects to `xtquant` to download historical data.
    - `load_from_csv(...)`: Reads from `storage/data/`.
  - **Caching**: Data is stored as CSV files in `storage/data/{period}/{ticker}.csv`.

### 2. Strategy Module (`src/strategy/`)
Contains the trading logic. All strategies must inherit from `BaseStrategy`.

- **`base_strategy.py`**:
  - Defines the abstract base class `BaseStrategy`.
  - **Key Method**: `on_bar(bar)` - Must be implemented by subclasses. Receives a dictionary/row of market data and returns a signal (`"buy"`, `"sell"`, or `"hold"`).
- **`ma_crossover.py`**:
  - Example implementation of a Moving Average Crossover strategy.
  - Calculates MA indicators and generates signals based on crossovers.

### 3. Backtest Module (`src/backtest/`)
Simulates trading strategies on historical data.

- **`engine.py`**:
  - Contains the `Backtester` class.
  - **Logic**: Event-driven loop iterating through historical bars.
  - **Features**:
    - **T+1 Enforcement**: Stocks bought today cannot be sold until tomorrow.
    - **Transaction Costs**: Calculates commission (buy/sell) and stamp duty (sell only).
    - **Position Management**: Tracks cash and share holdings.
    - **Next-Bar Execution**: Trades execute at next bar's open to avoid look-ahead bias. Signals generated on day N are executed on day N+1.
- **`runner.py`**:
  - Contains `BacktestRunner`.
  - Facilitates batch processing. Accepts a list of tickers, runs the backtest for each, and aggregates results into a summary DataFrame.
- **`performance.py`**:
  - Contains `PerformanceAnalyzer`.
  - Calculates metrics: Sharpe Ratio, Max Drawdown, Win Rate, Profit Factor, etc.

### 4. Live Trading Module (`src/live_trading/`)
Connects the strategy logic to real-time market execution.

- **`engine.py`**:
  - Contains `LiveTradeEngine`.
  - **Dependencies**: Requires `xtquant` library installed and Mini-QMT software running.
  - **Workflow**:
    1. Connects to QMT trading session (`XtQuantTrader`).
    2. Subscribes to real-time market data (`XtQuantSector`).
    3. On every new market tick/bar, calls the strategy's `on_bar`.
    4. If `on_bar` returns "buy"/"sell", places an actual order via QMT API.

## Key Workflows

### Backtesting Workflow
1. **Entry Point**: `run_analysis.py`
2. **Initialization**: `BacktestRunner` is instantiated.
3. **Data Loading**: `DataLoader` fetches data for requested tickers.
4. **Execution**: `Backtester` iterates through data, calling `strategy.on_bar()` for each timestamp.
5. **Result Aggregation**: Runner compiles metrics (Sharpe, Return, Max Drawdown) and saves to `backtest_summary.csv`.

### Live Trading Workflow
1. **Entry Point**: `run_live_trading.py`
2. **Setup**: User configures `MINI_QMT_PATH`, `ACCOUNT_ID`, and `SYMBOLS`.
3. **Connection**: `LiveTradeEngine` establishes a session with the local Mini-QMT client.
4. **Loop**: The engine enters a blocking loop, listening for market data callbacks.
5. **Signal Execution**: When a strategy triggers a signal, `engine.place_order` sends the instruction to the broker terminal.

## Extension Guide

- **Adding a New Strategy**: Create a new file in `src/strategy/`, inherit `BaseStrategy`, and implement `on_bar`.
- **Adding a New Data Source**: Modify `src/data/data_loader.py` to support other APIs (e.g., Tushare, BaoStock) if needed.
- **Customizing Metrics**: Edit `src/backtest/engine.py` inside `calculate_metrics()` to add new performance indicators.
