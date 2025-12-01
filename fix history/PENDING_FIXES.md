# Pending Fixes and Improvements

This document lists all known issues that need to be fixed and improvements to be made to the framework.

---

## 🔴 HIGH PRIORITY (Critical Issues)

### Issue #2: Hardcoded File Paths
**Status:** 🔴 NOT FIXED  
**Severity:** CRITICAL  
**File:** `src/data/data_loader.py` line 7

**Problem:**
```python
QMT_PYTHON_PATH = r"C:\国金QMT交易端模拟\bin.x64\Lib\site-packages"
```
- Framework fails on different machines
- Users must manually edit source code
- Not portable across different QMT installations

**Proposed Solution:**
1. Create `config.yaml` or `config.py` configuration file
2. Use environment variables: `QMT_PATH = os.getenv("QMT_PATH", default_path)`
3. Allow user configuration at runtime
4. Add setup wizard for first-time configuration

**Estimated Effort:** 2-3 hours

---

### Issue #3: No Position Sizing Framework
**Status:** 🔴 NOT FIXED  
**Severity:** CRITICAL  
**Files:** 
- `src/backtest/engine.py` line 138-145
- `src/live_trading/engine.py` line 189

**Problem:**
- Backtest: Always buys with 99% of available cash
- Live trading: Always buys exactly 100 shares
- No risk control per trade
- Cannot allocate portfolio across multiple positions

**Current Code:**
```python
# Backtest - buys maximum possible
max_qty = int((self.cash * 0.99) / exec_price)
quantity = (max_qty // 100) * 100

# Live trading - fixed 100 shares
cost = price * 100
```

**Proposed Solution:**
Create `PositionSizer` class with methods:
- **Fixed Fractional**: Trade X% of portfolio per position
- **Fixed Amount**: Trade fixed dollar amount
- **Risk-based**: Risk X% of capital per trade (requires stop-loss)
- **Kelly Criterion**: Optimal position sizing based on win rate
- **Equal Weight**: Divide capital equally across N positions

**Example API:**
```python
position_sizer = PositionSizer(
    method='fixed_fraction',
    fraction=0.1,  # 10% per trade
    max_positions=5
)

quantity = position_sizer.calculate(
    capital=10000,
    price=100,
    risk_per_share=5  # for risk-based sizing
)
```

**Estimated Effort:** 1-2 days

---

### Issue #4: No Risk Management System
**Status:** 🔴 NOT FIXED  
**Severity:** CRITICAL  
**Impact:** Can blow up accounts in live trading

**Missing Features:**
1. **Stop-Loss Orders**
   - Per-trade stop loss
   - Trailing stops
   - Time-based stops

2. **Take-Profit Orders**
   - Fixed target
   - Trailing profit locks
   - Scale-out at multiple targets

3. **Portfolio-Level Limits**
   - Maximum daily loss (e.g., -5%)
   - Maximum drawdown (e.g., -15%)
   - Position concentration limits (e.g., max 20% per stock)

4. **Trade Limits**
   - Maximum trades per day
   - Minimum time between trades
   - Maximum position size

**Proposed Solution:**
Create `RiskManager` class:
```python
class RiskManager:
    def __init__(self):
        self.max_position_pct = 0.2  # 20% max per position
        self.max_daily_loss = 0.05   # 5% max daily loss
        self.max_drawdown = 0.15     # 15% max drawdown
        self.stop_loss_pct = 0.02    # 2% stop loss
        
    def check_trade_allowed(self, signal, portfolio):
        # Check all risk constraints
        # Return True/False + reason
        pass
        
    def get_stop_loss_price(self, entry_price, direction):
        # Calculate stop loss price
        pass
```

**Estimated Effort:** 3-5 days

---

### Issue #5: No Order State Tracking in Live Trading
**Status:** 🔴 NOT FIXED  
**Severity:** HIGH  
**File:** `src/live_trading/engine.py`

**Problem:**
- Orders are placed but status unknown
- Don't know if order was filled, rejected, or partially filled
- Cannot react to order failures
- Cannot verify execution prices

**Current Behavior:**
```python
order_id = self.order_manager.buy(symbol, price, 100, "Strategy")
# Order ID returned but never checked again!
```

**Proposed Solution:**
1. Add order status callback handlers
2. Maintain order state machine: `pending → filled/rejected/cancelled`
3. Log all order lifecycle events
4. Add retry logic for failed orders
5. Verify execution prices match expectations

**Order States:**
```
PENDING → SUBMITTED → PARTIAL_FILLED → FILLED
                   ↘ REJECTED
                   ↘ CANCELLED
```

**Example API:**
```python
class OrderManager:
    def __init__(self):
        self.orders = {}  # order_id → Order object
        
    def on_order_filled(self, order_id, fill_price, fill_qty):
        # Callback when order fills
        self.orders[order_id].status = 'FILLED'
        self.logger.info(f"Order {order_id} filled")
        
    def get_order_status(self, order_id):
        return self.orders[order_id].status
```

**Estimated Effort:** 2-3 days

---

## 🟡 MEDIUM PRIORITY (Important Improvements)

### Issue #6: No Strategy State Persistence
**Status:** 🔴 NOT FIXED  
**Severity:** MEDIUM  
**Impact:** Live trading restart loses all strategy state

**Problem:**
- Strategy maintains price history, indicators in memory
- If live trading engine restarts, all state is lost
- Strategy must "warm up" again with historical data
- Potential for incorrect signals after restart

**Example:**
```python
class MACrossoverStrategy:
    def __init__(self):
        self.prices = []  # ← Lost on restart!
        self.short_ma = 0.0
        self.long_ma = 0.0
```

**Proposed Solution:**
1. Add `save_state()` and `load_state()` methods to `BaseStrategy`
2. Serialize strategy state to disk periodically (e.g., every minute)
3. Load state automatically on engine restart
4. Use pickle or JSON for serialization

**Example API:**
```python
class BaseStrategy:
    def save_state(self, filepath):
        state = {
            'prices': self.prices,
            'indicators': self.indicators,
            'timestamp': datetime.now()
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
    
    def load_state(self, filepath):
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        self.prices = state['prices']
        # ... restore state
```

**Estimated Effort:** 1-2 days

---

### Issue #7: No Parameter Optimization Framework
**Status:** 🔴 NOT FIXED  
**Severity:** MEDIUM  
**Impact:** Manual parameter tuning is slow and prone to overfitting

**Problem:**
- Users must manually try different parameter combinations
- No systematic way to find optimal parameters
- Risk of overfitting to historical data
- No validation methodology

**Proposed Solution:**
Create `Optimizer` class with methods:

1. **Grid Search**
```python
optimizer = GridSearchOptimizer(
    strategy_cls=MACrossoverStrategy,
    param_grid={
        'short_window': [5, 10, 15, 20],
        'long_window': [20, 30, 40, 50]
    },
    metric='sharpe_ratio'
)

results = optimizer.optimize(data, initial_capital=100000)
best_params = results['best_params']
```

2. **Walk-Forward Analysis**
- Train on in-sample data
- Test on out-of-sample data
- Prevents overfitting

3. **Genetic Algorithm**
- For large parameter spaces
- More efficient than grid search

**Features:**
- Parallel processing for speed
- Save optimization results to CSV
- Visualization of parameter sensitivity
- Cross-validation

**Estimated Effort:** 5-7 days

---

### Issue #8: Weak Error Handling
**Status:** 🔴 NOT FIXED  
**Severity:** MEDIUM  
**Files:** Multiple (runner.py, data_loader.py, live_trading/engine.py)

**Problem:**
```python
# runner.py line 95 - too generic
try:
    # ... complex operations
except Exception as e:
    print(f"Error processing {ticker}: {e}")
    # Swallows all errors!
```

**Issues:**
- Bare `except Exception` swallows all errors
- Silent failures in data loading
- No retry logic for network errors
- Poor error messages for debugging

**Proposed Solution:**
1. Use specific exception types
2. Add custom exceptions:
   ```python
   class DataFetchError(Exception): pass
   class OrderPlacementError(Exception): pass
   class InsufficientFundsError(Exception): pass
   ```
3. Implement retry logic with exponential backoff
4. Log full stack traces
5. Add error recovery strategies

**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_data_with_retry(symbol):
    try:
        return xtdata.get_market_data(symbol)
    except NetworkError as e:
        logger.warning(f"Network error, retrying: {e}")
        raise  # Triggers retry
    except DataNotFoundError as e:
        logger.error(f"Data not found: {e}")
        return None  # Don't retry
```

**Estimated Effort:** 2-3 days

---

### Issue #9: No Testing Infrastructure
**Status:** 🔴 NOT FIXED  
**Severity:** MEDIUM  
**Impact:** Cannot verify correctness, hard to catch regressions

**Missing:**
- Unit tests for each module
- Integration tests
- Mock QMT API for testing without broker
- Regression tests for known bugs

**Proposed Solution:**
Create `tests/` directory with:
```
tests/
├── test_backtest_engine.py
├── test_data_loader.py
├── test_strategies.py
├── test_position_sizing.py
├── test_risk_manager.py
├── test_live_trading.py
└── mocks/
    └── mock_qmt.py
```

**Example Test:**
```python
import pytest
from src.backtest.engine import Backtester

def test_t1_rule():
    """Test that T+1 rule prevents same-day selling"""
    # Create test data
    # Create strategy that buys and immediately tries to sell
    # Assert sell order is not executed same day
    pass

def test_commission_calculation():
    """Test commission and stamp duty are calculated correctly"""
    # Test with known values
    # Assert final capital matches expected
    pass
```

**Coverage Target:** >80% code coverage

**Estimated Effort:** 5-7 days

---

## 🟢 LOW PRIORITY (Nice-to-Have)

### Issue #10: Limited Performance Metrics
**Status:** 🔴 NOT FIXED  
**File:** `src/backtest/performance.py`

**Current Metrics:**
- Total Return
- Sharpe Ratio
- Max Drawdown
- Win Rate
- Avg Win/Loss
- Profit Factor

**Missing Metrics:**
- **Sortino Ratio** (downside deviation only)
- **Calmar Ratio** (return / max drawdown)
- **Information Ratio** (vs benchmark)
- **Maximum Adverse Excursion (MAE)** - worst intra-trade drawdown
- **Maximum Favorable Excursion (MFE)** - best intra-trade profit
- **Ulcer Index** - drawdown severity
- **Recovery Time** - time to recover from drawdown
- **Rolling Returns** - performance over time windows

**Estimated Effort:** 2-3 days

---

### Issue #11: Basic Visualization
**Status:** 🔴 NOT FIXED  
**File:** `src/backtest/plotting.py`

**Current Limitations:**
- No trade markers on price charts
- No indicator overlays (MA, Bollinger Bands)
- Static matplotlib plots (not interactive)
- Cannot zoom or inspect details

**Proposed Improvements:**
1. **Trade Markers**
   - Green arrows for buys
   - Red arrows for sells
   - Tooltip with trade details

2. **Indicator Overlays**
   - Plot MAs on price chart
   - Show Bollinger Bands, RSI, MACD

3. **Interactive Plots**
   - Use Plotly instead of matplotlib
   - Zoom, pan, hover tooltips
   - Export to HTML

4. **Performance Tear Sheet**
   - Similar to Pyfolio library
   - Single-page comprehensive report
   - Returns distribution, rolling metrics

**Estimated Effort:** 3-4 days

---

### Issue #12: Single Data Source Dependency
**Status:** 🔴 NOT FIXED  
**File:** `src/data/data_loader.py`

**Problem:**
- Only supports Mini-QMT (xtquant)
- If QMT is down, entire system fails
- Cannot use alternative data providers

**Proposed Solution:**
Create data provider abstraction:
```python
class DataProvider(ABC):
    @abstractmethod
    def fetch_data(self, symbol, start, end, period):
        pass

class QMTDataProvider(DataProvider):
    def fetch_data(self, symbol, start, end, period):
        # Use xtquant
        pass

class TushareDataProvider(DataProvider):
    def fetch_data(self, symbol, start, end, period):
        # Use Tushare API
        pass

class AkShareDataProvider(DataProvider):
    def fetch_data(self, symbol, start, end, period):
        # Use AkShare
        pass

# Usage
data_manager = DataManager(provider=TushareDataProvider())
```

**Alternative Sources:**
- Tushare (free for A-shares)
- AkShare (open source)
- Yahoo Finance (limited A-share support)

**Estimated Effort:** 2-3 days per provider

---

### Issue #13: No Portfolio-Level Backtesting
**Status:** 🔴 NOT FIXED  
**Impact:** Can only test one ticker at a time

**Current Limitation:**
```python
# Can only do this:
backtest_single_ticker('000001.SZ', strategy)

# Cannot do this:
backtest_portfolio(['000001.SZ', '600519.SH', '159919.SZ'], strategy)
```

**Proposed Solution:**
1. **Multi-Asset Engine**
   - Track positions for multiple stocks simultaneously
   - Shared cash pool
   - Portfolio-level rebalancing

2. **Features:**
   - Correlation analysis
   - Portfolio optimization
   - Rebalancing strategies (periodic, threshold-based)
   - Sector diversification

**Example API:**
```python
portfolio_engine = PortfolioBacktester(
    symbols=['000001.SZ', '600519.SH', '159919.SZ'],
    strategy=strategy,
    rebalance_frequency='monthly',
    equal_weight=True
)

results = portfolio_engine.run()
```

**Estimated Effort:** 5-7 days

---

## Summary

### Priority Breakdown
- **Critical (HIGH):** 5 issues - Estimated 10-15 days
- **Important (MEDIUM):** 4 issues - Estimated 15-20 days  
- **Nice-to-Have (LOW):** 4 issues - Estimated 12-17 days

### Total Estimated Effort
**37-52 days** (approximately 2-3 months for one developer)

### Recommended Fix Order
1. ✅ Issue #1 - Look-ahead bias (COMPLETED)
2. Issue #2 - Hardcoded paths (quick fix)
3. Issue #4 - Risk management (critical for live trading)
4. Issue #3 - Position sizing (critical for live trading)
5. Issue #5 - Order tracking (critical for live trading)
6. Issue #8 - Error handling (improves reliability)
7. Issue #9 - Testing infrastructure (prevents regressions)
8. Issue #7 - Parameter optimization (improves strategy development)
9. Issue #6 - State persistence (nice for live trading)
10. Issues #10-13 - Lower priority enhancements

---

*Last Updated: November 30, 2025*
