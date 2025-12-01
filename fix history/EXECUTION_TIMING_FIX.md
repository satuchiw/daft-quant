# Look-Ahead Bias Fix - Execution Timing

## Problem Identified

**Previous Behavior (INCORRECT):**
```python
# Day 1, 3:00 PM - Bar closes
bar = {'close': 100.0, 'open': 98.0, ...}

signal = strategy.on_bar(bar)  # Strategy sees close = 100.0
# Returns "buy"

# ❌ PROBLEM: Executed IMMEDIATELY at close price (100.0)
execute_trade(price=100.0, datetime='2024-01-01 15:00')
```

**Issue:** This creates **look-ahead bias** because:
1. Strategy sees the close price (100.0)
2. Strategy makes decision based on that close
3. Trade executes at that same close price
4. **In reality, you cannot trade at 3:00 PM after market closes!**

## Solution Implemented

**New Behavior (CORRECT):**
```python
# Day 1, 3:00 PM - Bar closes
bar = {'close': 100.0, 'open': 98.0, ...}

signal = strategy.on_bar(bar)  # Strategy sees close = 100.0
# Returns "buy"

# ✓ Signal STORED, not executed yet
pending_signal = "buy"

# --- Next Day ---
# Day 2, 9:30 AM - Market opens
next_bar = {'open': 101.5, ...}  # Price may gap up/down overnight

# ✓ NOW execute the pending buy signal at Day 2's open
execute_trade(price=101.5, datetime='2024-01-02 09:30')
```

**Benefits:**
1. **Realistic execution timing** - matches real-world trading
2. **Accounts for overnight gaps** - price can change between signal and execution
3. **Eliminates look-ahead bias** - cannot use information you wouldn't have in reality
4. **More conservative results** - backtest results are now more accurate

## Code Changes

### Modified File: `src/backtest/engine.py`

**Added pending signal mechanism:**
```python
# State variables
self.pending_signal = None
self.pending_signal_data = None
```

**Modified execution flow:**
```python
for i in range(len(self.data)):
    # 1. Execute pending signal from PREVIOUS bar at CURRENT bar's open
    if self.pending_signal is not None:
        exec_price = bar['open']  # ← Key change: use NEXT bar's open
        if self.pending_signal == "buy":
            self._buy(exec_price, exec_date, qty)
    
    # 2. Generate new signal from current bar
    signal = self.strategy.on_bar(bar)
    
    # 3. Store signal for NEXT bar (don't execute now)
    if signal == "buy" or signal == "sell":
        self.pending_signal = signal  # Will execute next iteration
```

## Impact on Results

### Expected Changes in Backtest Metrics:
- **Total Return**: May decrease slightly (more realistic execution prices)
- **Win Rate**: May change (some trades execute at worse prices due to gaps)
- **Sharpe Ratio**: Should be more accurate
- **Trade Count**: May decrease by 1 (last signal never executes if no next bar)

### Example Comparison:

**Before Fix (Look-Ahead Bias):**
- Signal on 2024-01-15 @ close=100.0 → Execute @ 100.0
- Profit if price goes to 110.0 = 10%

**After Fix (Realistic):**
- Signal on 2024-01-15 @ close=100.0
- Execute on 2024-01-16 @ open=101.5 (gap up)
- Profit if price goes to 110.0 = 8.37%

The fix makes results **more conservative and realistic**.

## Testing

Run the test script to verify:
```bash
python test_execution_timing.py
```

Expected output should show:
- Signals generated on Day N
- Trades executed on Day N+1
- Execution prices match next bar's open

## For Strategy Developers

Your strategy code **does not need to change**! The execution timing is handled by the backtest engine.

However, be aware:
```python
def on_bar(self, bar):
    close = bar['close']
    if close < 95:
        return "buy"  # ← This will execute TOMORROW at market open
```

**Important:**
- Signal generated when you see the close price
- Trade executes at **next bar's open** (not at current close)
- There may be price slippage between close and next open

## Intraday vs Daily Trading

### Daily Bars (`period='1d'`)
- **Signal Generation**: 3:00 PM when bar closes
- **Execution**: Next day 9:30 AM at market open
- **Delay**: ~18.5 hours

### Minute Bars (`period='1m'`)
- **Signal Generation**: End of minute (e.g., 10:00:59)
- **Execution**: Next minute open (e.g., 10:01:00)
- **Delay**: ~1 second

The fix is most important for daily bars, but applies to all timeframes.

## Related Documentation

- See `USER_MANUAL.md` Section "Important: Trade Execution Timing"
- See `DEVELOPER_HANDBOOK.md` for technical details
- Run `test_execution_timing.py` for verification
