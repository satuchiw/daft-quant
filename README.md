# Quantitative Trading System

## Project Overview
This project is a comprehensive quantitative trading system designed to handle the entire lifecycle of algorithmic trading, specifically optimized for **Chinese A-shares**. It covers data acquisition, strategy development, and high-fidelity backtesting.

## Modules Status

### ✅ 1. Data Storage and Acquisition
**Implementation:** `src/data/`
- **Source:** Mini-QMT (`xtquant`).
- **Features:** 
  - Automatic incremental downloading.
  - Local CSV caching for offline access.
  - Support for intraday and daily bars.

### ✅ 2. Strategy Module
**Implementation:** `src/strategy/`
- **Design:** Strategies are **independent signal generators** inheriting from `BaseStrategy`.
- **Key Method:** `on_bar(bar)` returns "buy", "sell", or "hold".
- **Implemented Strategies:**
  - Moving Average Crossover (`MACrossoverStrategy`)
  - RSI Strategy (`RSIStrategy`)
- **Compatibility:** Same strategy code runs in Backtest and Live Trading.

### ✅ 3. Backtest Module
**Implementation:** `src/backtest/`
- **Engine:** Event-driven backtester (`Backtester`).
- **Features:**
  - **A-Share Rules:** Enforced **T+1** trading logic.
  - **Costs:** Configurable commission, stamp duty (sell-side), and slippage.
  - **Batch Processing:** `BacktestRunner` allows testing multiple stocks/ETFs in one go.
  - **Reporting:** Comprehensive metrics (Sharpe, Drawdown, Win Rate) and visualizations.

### 🚧 4. Live Trading Interface
**Status:** Planned
- Will connect strategy signals to Mini-QMT execution API.
- Real-time order management and position monitoring.

## Project Structure
```
real quant/
├── src/
│   ├── backtest/       # Backtest engine and runner
│   ├── data/           # Data fetching and storage logic
│   └── strategy/       # Strategy logic (MA, RSI, etc.)
├── storage/
│   └── data/           # Cached market data (CSV)
├── run_analysis.py     # Script to run batch backtests
├── main.py             # Data fetching demo
└── README.md
```

## Quick Start

**1. Run a Backtest:**
Use the provided `run_analysis.py` to test a strategy on a list of tickers.
```bash
python run_analysis.py
```
This will:
1. Fetch data for defined tickers (e.g., '000001.SZ').
2. Run the `MACrossoverStrategy`.
3. Display a performance summary table.

**2. Create a New Strategy:**
Inherit from `BaseStrategy` in `src/strategy/` and implement `on_bar`.
```python
from .base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def on_bar(self, bar):
        if bar['close'] > 20:
            return "buy"
        return "hold"
```
