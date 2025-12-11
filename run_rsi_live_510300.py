"""
RSI Live Trading Script for 510300.SH (CSI 300 ETF)
5-Minute Data - Paper Trading with T+1 Enforcement

Configuration:
- Symbol: 510300.SH (CSI 300 ETF)
- Period: 5m (5-minute bars)
- Strategy: RSI (period=14, overbought=70, oversold=30)
- Account: 40688525 (Paper Trading)

Strategy Logic:
- BUY when RSI < 30 (Oversold)
- SELL when RSI > 70 (Overbought)

T+1 Enforcement:
- Shares bought today CANNOT be sold until tomorrow
- System uses can_use_volume from position query
- Sell signals are ignored if can_use_volume = 0

Prerequisites:
- Mini-QMT must be running and logged in BEFORE this script starts
- xtquant must be installed
"""

import sys
import os
import time
from datetime import datetime
import logging

# Add project root to path for proper imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.live_trading import LiveTradeEngine, TradeLogger
from src.strategy.rsi_strategy import RSIStrategy

# ============== CONFIGURATION ==============
# Mini-QMT Path
MINI_QMT_PATH = r"E:\mquant\QT\国金QMT交易端模拟\userdata_mini"

# Account credentials
ACCOUNT_ID = "40688525"

# Trading target
SYMBOL = "510300.SH"  # CSI 300 ETF
PERIOD = "5m"         # 5-minute bars

# RSI Strategy Parameters
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0

# Order Parameters
ORDER_VOLUME = 100           # Shares per order
MAX_POSITION = 50000         # Maximum position size (current: 30000)
ENABLE_TRADING = True        # Set to False for signal-only mode

# Market Hours (China A-Share)
MARKET_OPEN_MORNING = "09:30"
MARKET_CLOSE_MORNING = "11:30"
MARKET_OPEN_AFTERNOON = "13:00"
MARKET_CLOSE_AFTERNOON = "15:00"

# Log file with date
LOG_FILE = f"live_trading_510300_{datetime.now().strftime('%Y%m%d')}.log"
# ===========================================


def is_market_hours() -> bool:
    """Check if current time is within market hours."""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    # Morning session: 09:30 - 11:30
    if MARKET_OPEN_MORNING <= current_time <= MARKET_CLOSE_MORNING:
        return True
    # Afternoon session: 13:00 - 15:00
    if MARKET_OPEN_AFTERNOON <= current_time <= MARKET_CLOSE_AFTERNOON:
        return True
    return False


def wait_for_market_open(logger: TradeLogger) -> bool:
    """
    Wait until market opens.
    
    Returns:
        True if market is open, False if market closed for the day
    """
    while not is_market_hours():
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # If before morning open, wait
        if current_time < MARKET_OPEN_MORNING:
            wait_seconds = 30
            logger.info(f"Market not open yet. Current: {current_time}. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
        # If in lunch break, wait
        elif MARKET_CLOSE_MORNING < current_time < MARKET_OPEN_AFTERNOON:
            wait_seconds = 60
            logger.info(f"Lunch break. Current: {current_time}. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
        # If after close, exit
        elif current_time > MARKET_CLOSE_AFTERNOON:
            logger.info(f"Market closed for today ({current_time}). Exiting.")
            return False
    return True


def print_banner():
    """Print startup banner."""
    print("=" * 70)
    print("  RSI Live Trading System - 510300.SH (CSI 300 ETF)")
    print("=" * 70)
    print(f"  Symbol:       {SYMBOL}")
    print(f"  Period:       {PERIOD}")
    print(f"  Account:      {ACCOUNT_ID} (Paper Trading)")
    print(f"  RSI Config:   period={RSI_PERIOD}, overbought={RSI_OVERBOUGHT}, oversold={RSI_OVERSOLD}")
    print(f"  Order Volume: {ORDER_VOLUME}")
    print(f"  Max Position: {MAX_POSITION}")
    print(f"  Trading:      {'ENABLED' if ENABLE_TRADING else 'DISABLED (Signal Only)'}")
    print("=" * 70)
    print()
    print("  Strategy Logic:")
    print(f"    - BUY  when RSI < {RSI_OVERSOLD} (Oversold)")
    print(f"    - SELL when RSI > {RSI_OVERBOUGHT} (Overbought)")
    print()
    print("  T+1 Enforcement:")
    print("    - Shares bought today CANNOT be sold until tomorrow")
    print("    - System checks can_use_volume before any sell order")
    print("=" * 70)
    print()


def main():
    """Main entry point for live trading."""
    print_banner()
    
    # Initialize logger
    logger = TradeLogger(
        name="RSI_Live_510300",
        log_file=LOG_FILE
    )
    
    logger.info("=" * 60)
    logger.info("RSI Live Trading Script Started")
    logger.info(f"Symbol: {SYMBOL}")
    logger.info(f"Period: {PERIOD}")
    logger.info(f"Account: {ACCOUNT_ID} (Paper Trading)")
    logger.info(f"RSI Config: period={RSI_PERIOD}, overbought={RSI_OVERBOUGHT}, oversold={RSI_OVERSOLD}")
    logger.info(f"Trading Enabled: {ENABLE_TRADING}")
    logger.info("=" * 60)
    
    # Wait for market if started early
    if not wait_for_market_open(logger):
        return
    
    logger.info("Market is open. Initializing trading engine...")
    
    # Initialize RSI Strategy
    strategy = RSIStrategy(
        period=RSI_PERIOD,
        overbought=RSI_OVERBOUGHT,
        oversold=RSI_OVERSOLD
    )
    
    # Initialize Live Trade Engine
    engine = LiveTradeEngine(
        strategy=strategy,
        account_id=ACCOUNT_ID,
        mini_qmt_path=MINI_QMT_PATH,
        symbols=[SYMBOL],
        period=PERIOD,
        log_file=LOG_FILE,
        order_volume=ORDER_VOLUME,
        max_position_per_symbol=MAX_POSITION,
        enable_trading=ENABLE_TRADING
    )
    
    # Start Trading
    try:
        logger.info("Connecting to Mini-QMT...")
        if engine.connect():
            logger.info("Connection successful!")
            
            # Print initial portfolio status
            logger.info("Initial Portfolio Status:")
            engine.get_portfolio_status()
            
            # Start trading loop
            logger.info("Starting trading loop...")
            engine.start()
        else:
            logger.error("Failed to connect to Mini-QMT.")
            logger.error("Please ensure:")
            logger.error("  1. Mini-QMT is running")
            logger.error("  2. You are logged in")
            logger.error(f"  3. Path is correct: {MINI_QMT_PATH}")
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("Trading session ended.")
        logger.info(f"Log file: {LOG_FILE}")


if __name__ == "__main__":
    main()
