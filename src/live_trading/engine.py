"""
Live Trading Engine for Mini-QMT.
Manages data subscription, strategy execution, and order placement with T+1 enforcement.
"""

import time
import traceback
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from threading import Thread, Event

try:
    from xtquant import xtdata, xttrader, xttype, xtconstant
    XTQUANT_AVAILABLE = True
except ImportError:
    print("Warning: xtquant not found.")
    XTQUANT_AVAILABLE = False

from ..strategy.base_strategy import BaseStrategy
from .order_manager import OrderManager
from .logger import TradeLogger


class LiveTradeEngine:
    """
    Core engine for live trading using Mini-QMT.
    
    Features:
    - Stable data connection with reconnection handling
    - RSI-based signal generation
    - T+1 settlement enforcement
    - Comprehensive logging
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        account_id: str,
        mini_qmt_path: str,
        symbols: List[str],
        period: str = '5m',
        log_file: str = 'live_trading.log',
        order_volume: int = 100,
        max_position_per_symbol: int = 1000,
        enable_trading: bool = True
    ):
        """
        Initialize Live Trade Engine.
        
        Args:
            strategy: Instance of BaseStrategy (e.g., RSIStrategy)
            account_id: QMT Account ID
            mini_qmt_path: Path to userdata_mini directory
            symbols: List of stocks to trade (e.g., ['510300.SH'])
            period: Data period ('5m' for 5-minute bars)
            log_file: Path to log file
            order_volume: Volume per order (default 100)
            max_position_per_symbol: Maximum position size per symbol
            enable_trading: If False, only generate signals without placing orders
        """
        # Initialize TradeLogger
        self.trade_logger = TradeLogger(
            name="LiveEngine",
            log_file=log_file
        )
        
        self.strategy = strategy
        self.account_id = account_id
        self.mini_qmt_path = mini_qmt_path
        self.symbols = symbols
        self.period = period
        self.order_volume = order_volume
        self.max_position_per_symbol = max_position_per_symbol
        self.enable_trading = enable_trading
        
        # Components
        self.xt_trader = None
        self.order_manager = None
        self.running = False
        self.connected = False
        
        # Data tracking
        self.last_bar_time: Dict[str, datetime] = {}
        self.historical_data: Dict[str, List[Dict]] = {s: [] for s in symbols}
        
        # Connection management
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Stop event for clean shutdown
        self.stop_event = Event()
        
        # Initialize Strategy
        self.trade_logger.info(f"Initializing Strategy: {strategy.__class__.__name__}")
        self.strategy.on_init()
        
        self.trade_logger.info(f"LiveTradeEngine initialized for symbols: {symbols}")
        self.trade_logger.info(f"Period: {period}, Order Volume: {order_volume}, Trading Enabled: {enable_trading}")

    def connect(self) -> bool:
        """
        Connect to Mini-QMT Trader with retry logic.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not XTQUANT_AVAILABLE:
            self.trade_logger.error("xtquant library not available. Cannot connect.")
            return False
        
        self.trade_logger.info(f"Connecting to Mini-QMT with account {self.account_id}...")
        self.trade_logger.log_connection("CONNECTING", f"Path: {self.mini_qmt_path}")
        
        try:
            # Generate unique session ID
            session_id = int(time.time() * 1000) % 1000000
            
            # Create Trader instance
            self.xt_trader = xttrader.XtQuantTrader(self.mini_qmt_path, session_id)
            
            # Register callbacks
            self._register_callbacks()
            
            # Start Trader
            self.xt_trader.start()
            
            # Connect
            connect_result = self.xt_trader.connect()
            if connect_result == 0:
                self.trade_logger.log_connection("CONNECTED", "Mini-QMT connection successful")
                self.connected = True
            else:
                self.trade_logger.log_connection("FAILED", f"Connection failed with code: {connect_result}")
                return False
            
            # Subscribe to Account
            acc = xttype.StockAccount(self.account_id)
            subscribe_result = self.xt_trader.subscribe(acc)
            self.trade_logger.info(f"Account subscription result: {subscribe_result}")
            
            # Initialize Order Manager with TradeLogger
            self.order_manager = OrderManager(
                self.xt_trader,
                self.account_id,
                self.trade_logger
            )
            
            self.reconnect_attempts = 0
            return True
            
        except Exception as e:
            self.trade_logger.log_connection("ERROR", f"Connection exception: {str(e)}")
            self.trade_logger.error(traceback.format_exc())
            return False

    def _register_callbacks(self):
        """Register xtquant callbacks for order status updates."""
        if self.xt_trader is None:
            return
        
        # Create callback class
        class MyXtQuantTraderCallback:
            def __init__(self, engine):
                self.engine = engine
            
            def on_disconnected(self):
                self.engine.trade_logger.log_connection("DISCONNECTED", "Lost connection to Mini-QMT")
                self.engine.connected = False
                self.engine._handle_disconnection()
            
            def on_stock_order(self, order):
                self.engine.trade_logger.info(
                    f"Order Update: {order.stock_code} | Status: {order.order_status} | "
                    f"OrderID: {order.order_id}"
                )
            
            def on_stock_trade(self, trade):
                self.engine.trade_logger.log_order_filled(
                    symbol=trade.stock_code,
                    signal_type="BUY" if trade.order_type == xtconstant.STOCK_BUY else "SELL",
                    price=trade.traded_price,
                    volume=trade.traded_volume,
                    order_id=str(trade.order_id)
                )
            
            def on_order_error(self, order_error):
                self.engine.trade_logger.error(
                    f"Order Error: {order_error.order_id} | Code: {order_error.error_id} | "
                    f"Msg: {order_error.error_msg}"
                )
            
            def on_order_stock_async_response(self, response):
                self.engine.trade_logger.debug(f"Async order response: {response}")
        
        callback = MyXtQuantTraderCallback(self)
        self.xt_trader.register_callback(callback)

    def _handle_disconnection(self):
        """Handle disconnection with reconnection attempts."""
        if self.stop_event.is_set():
            return
        
        while self.reconnect_attempts < self.max_reconnect_attempts and not self.stop_event.is_set():
            self.reconnect_attempts += 1
            self.trade_logger.warning(
                f"Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})..."
            )
            
            time.sleep(self.reconnect_delay)
            
            if self.connect():
                self.trade_logger.info("Reconnection successful!")
                return
        
        self.trade_logger.error("Max reconnection attempts reached. Stopping engine.")
        self.stop()

    def start(self):
        """
        Start the trading loop.
        Subscribes to market data and processes signals.
        """
        if not self.connected:
            if not self.connect():
                self.trade_logger.error("Failed to connect. Cannot start trading.")
                return
        
        self.running = True
        self.stop_event.clear()
        
        self.trade_logger.info("=" * 60)
        self.trade_logger.info("Starting Live Trading Engine")
        self.trade_logger.info(f"Symbols: {self.symbols}")
        self.trade_logger.info(f"Period: {self.period}")
        self.trade_logger.info(f"Trading Enabled: {self.enable_trading}")
        self.trade_logger.info("=" * 60)
        
        # Load historical data for strategy warmup
        self._load_historical_data()
        
        # Subscribe to market data
        for symbol in self.symbols:
            self.trade_logger.info(f"Subscribing to {symbol} ({self.period})")
            try:
                xtdata.subscribe_quote(
                    symbol,
                    period=self.period,
                    count=-1,
                    callback=self._on_market_data
                )
            except Exception as e:
                self.trade_logger.error(f"Failed to subscribe to {symbol}: {e}")
        
        # Main loop
        self.trade_logger.info("Entering main trading loop...")
        try:
            while self.running and not self.stop_event.is_set():
                # Periodic health check
                self._health_check()
                time.sleep(1)
        except KeyboardInterrupt:
            self.trade_logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def _load_historical_data(self):
        """Load historical data for strategy warmup."""
        self.trade_logger.info("Loading historical data for strategy warmup...")
        
        for symbol in self.symbols:
            try:
                # Get historical bars for RSI calculation warmup
                # Need at least RSI period + buffer bars
                bars_needed = 50  # Enough for RSI-14 warmup
                
                # Use xtdata.get_market_data_ex for historical data
                # This returns data in a more usable format
                data = xtdata.get_market_data_ex(
                    field_list=[],  # Empty = all fields
                    stock_list=[symbol],
                    period=self.period,
                    count=bars_needed
                )
                
                if data and symbol in data:
                    symbol_data = data[symbol]
                    if len(symbol_data) > 0:
                        self.trade_logger.info(f"Loaded {len(symbol_data)} historical bars for {symbol}")
                        
                        # Process historical bars through strategy for warmup
                        for idx in range(len(symbol_data)):
                            row = symbol_data.iloc[idx]
                            bar = {
                                'datetime': row.name if hasattr(row, 'name') else datetime.now(),
                                'open': float(row.get('open', 0)),
                                'high': float(row.get('high', 0)),
                                'low': float(row.get('low', 0)),
                                'close': float(row.get('close', 0)),
                                'volume': float(row.get('volume', 0))
                            }
                            # Feed to strategy for warmup (don't execute signals)
                            self.strategy.on_bar(bar)
                        
                        self.trade_logger.info(f"Strategy warmed up with {len(symbol_data)} bars")
                    else:
                        self.trade_logger.warning(f"No historical data available for {symbol}")
                else:
                    self.trade_logger.warning(f"Could not load historical data for {symbol}")
                    
            except Exception as e:
                self.trade_logger.warning(f"Could not load historical data for {symbol}: {e}")
                import traceback
                self.trade_logger.debug(traceback.format_exc())

    def _on_market_data(self, data: Dict):
        """
        Callback when new market data arrives.
        
        Args:
            data: Market data from xtquant
        """
        for symbol, tick_data in data.items():
            if symbol not in self.symbols:
                continue
            
            try:
                bar = self._parse_market_data(symbol, tick_data)
                if bar is None:
                    continue
                
                # Check for duplicate bar
                bar_time = bar['datetime']
                if symbol in self.last_bar_time:
                    if bar_time <= self.last_bar_time[symbol]:
                        continue  # Skip duplicate
                
                self.last_bar_time[symbol] = bar_time
                
                # Log data received
                self.trade_logger.info(
                    f"[BAR] {symbol} @ {bar_time.strftime('%H:%M:%S')} | "
                    f"O:{bar['open']:.4f} H:{bar['high']:.4f} L:{bar['low']:.4f} "
                    f"C:{bar['close']:.4f} V:{bar['volume']:.0f}"
                )
                
                # Generate signal from strategy
                signal = self.strategy.on_bar(bar)
                
                # Get RSI value if available (for logging)
                rsi_value = None
                if hasattr(self.strategy, '_calculate_rsi'):
                    rsi_value = self.strategy._calculate_rsi()
                
                # Handle signal
                self._handle_signal(symbol, signal, bar['close'], rsi_value)
                
            except Exception as e:
                self.trade_logger.error(f"Error processing data for {symbol}: {e}")
                self.trade_logger.error(traceback.format_exc())

    def _parse_market_data(self, symbol: str, tick_data: Any) -> Optional[Dict]:
        """
        Parse market data from xtquant into standard bar format.
        
        xtquant subscribe_quote returns data in format:
        {
            'symbol': [
                {'time': ms_timestamp, 'open': x, 'high': x, 'low': x, 'close': x, 'volume': x, ...}
            ]
        }
        
        Returns:
            Bar dictionary or None if invalid
        """
        # Skip invalid data
        if tick_data is None or tick_data == 0 or tick_data == []:
            return None
        
        # Handle list format (from subscribe_quote with period)
        if isinstance(tick_data, list):
            if len(tick_data) == 0:
                return None
            
            # Get the latest bar
            latest_bar = tick_data[-1]
            
            # Check if it's a dict (new format from subscribe_quote)
            if isinstance(latest_bar, dict):
                timestamp = latest_bar.get('time', 0)
                if timestamp == 0:
                    return None
                
                # Handle millisecond timestamps
                if timestamp > 1e12:
                    bar_datetime = datetime.fromtimestamp(timestamp / 1000)
                else:
                    bar_datetime = datetime.fromtimestamp(timestamp)
                
                return {
                    'datetime': bar_datetime,
                    'open': float(latest_bar.get('open', 0)),
                    'high': float(latest_bar.get('high', 0)),
                    'low': float(latest_bar.get('low', 0)),
                    'close': float(latest_bar.get('close', 0)),
                    'volume': float(latest_bar.get('volume', 0))
                }
            
            # Handle list format (legacy format: [timestamp, open, high, low, close, volume, ...])
            elif isinstance(latest_bar, (list, tuple)):
                if len(latest_bar) < 6:
                    self.trade_logger.warning(f"Invalid bar data length for {symbol}: {len(latest_bar)}")
                    return None
                
                timestamp = latest_bar[0]
                if timestamp > 1e12:
                    bar_datetime = datetime.fromtimestamp(timestamp / 1000)
                else:
                    bar_datetime = datetime.fromtimestamp(timestamp)
                
                return {
                    'datetime': bar_datetime,
                    'open': float(latest_bar[1]),
                    'high': float(latest_bar[2]),
                    'low': float(latest_bar[3]),
                    'close': float(latest_bar[4]),
                    'volume': float(latest_bar[5])
                }
            else:
                self.trade_logger.warning(f"Unknown bar format for {symbol}: {type(latest_bar)}")
                return None
        
        # Handle single dict format (tick data)
        elif isinstance(tick_data, dict):
            # Check for bar data format (has 'close' key)
            if 'close' in tick_data:
                timestamp = tick_data.get('time', time.time() * 1000)
                if timestamp > 1e12:
                    bar_datetime = datetime.fromtimestamp(timestamp / 1000)
                else:
                    bar_datetime = datetime.fromtimestamp(timestamp)
                
                return {
                    'datetime': bar_datetime,
                    'open': float(tick_data.get('open', 0)),
                    'high': float(tick_data.get('high', 0)),
                    'low': float(tick_data.get('low', 0)),
                    'close': float(tick_data.get('close', 0)),
                    'volume': float(tick_data.get('volume', 0))
                }
            
            # Check for tick data format (has 'lastPrice' key)
            current_price = tick_data.get('lastPrice')
            if current_price:
                tick_time = tick_data.get('time', time.time() * 1000)
                if tick_time > 1e12:
                    bar_datetime = datetime.fromtimestamp(tick_time / 1000)
                else:
                    bar_datetime = datetime.fromtimestamp(tick_time)
                
                return {
                    'datetime': bar_datetime,
                    'open': tick_data.get('open', current_price),
                    'high': tick_data.get('high', current_price),
                    'low': tick_data.get('low', current_price),
                    'close': current_price,
                    'volume': tick_data.get('volume', 0)
                }
            
            return None
        
        else:
            self.trade_logger.warning(f"Unknown data format for {symbol}: {type(tick_data)}")
            return None

    def _handle_signal(
        self,
        symbol: str,
        signal: Any,
        price: float,
        rsi_value: Optional[float] = None
    ):
        """
        Handle trading signal from strategy.
        
        Args:
            symbol: Stock symbol
            signal: Signal from strategy ('buy', 'sell', 'hold')
            price: Current price
            rsi_value: Current RSI value (for logging)
        """
        if signal == "hold":
            if rsi_value is not None:
                self.trade_logger.info(f"[HOLD] {symbol} | RSI: {rsi_value:.2f} (30 < RSI < 70)")
            return
        
        # Log signal
        self.trade_logger.log_signal(
            symbol=symbol,
            signal_type=signal,
            price=price,
            rsi_value=rsi_value
        )
        
        if not self.enable_trading:
            self.trade_logger.info(f"Trading disabled. Signal logged but not executed: {signal}")
            return
        
        if self.order_manager is None:
            self.trade_logger.error("Order manager not initialized. Cannot execute signal.")
            return
        
        # Execute signal
        if signal == "buy":
            self._execute_buy(symbol, price, rsi_value)
        elif signal == "sell":
            self._execute_sell(symbol, price, rsi_value)

    def _execute_buy(self, symbol: str, price: float, rsi_value: Optional[float] = None):
        """Execute buy signal."""
        # Check current position
        position = self.order_manager.get_position(symbol)
        current_volume = position.volume if position else 0
        
        # Check max position limit
        if current_volume >= self.max_position_per_symbol:
            self.trade_logger.warning(
                f"Max position reached for {symbol}. Current: {current_volume}, Max: {self.max_position_per_symbol}"
            )
            return
        
        # Calculate order volume
        order_vol = min(self.order_volume, self.max_position_per_symbol - current_volume)
        order_vol = (order_vol // 100) * 100  # Round to lot size
        
        if order_vol < 100:
            self.trade_logger.warning(f"Order volume too small: {order_vol}")
            return
        
        # Place buy order
        success, order_id = self.order_manager.buy(
            symbol=symbol,
            price=price,
            quantity=order_vol,
            strategy_name="RSI_Strategy"
        )
        
        if success:
            rsi_str = f"{rsi_value:.2f}" if rsi_value is not None else "N/A"
            self.trade_logger.info(
                f"[BUY EXECUTED] {symbol} | Price: {price:.4f} | Vol: {order_vol} | "
                f"RSI: {rsi_str} | OrderID: {order_id}"
            )

    def _execute_sell(self, symbol: str, price: float, rsi_value: Optional[float] = None):
        """
        Execute sell signal with T+1 enforcement.
        
        CRITICAL: This method relies on OrderManager's T+1 enforcement.
        The OrderManager will check can_use_volume and reject sells for
        shares bought today.
        """
        # Get position info
        position = self.order_manager.get_position(symbol)
        
        if position is None:
            self.trade_logger.log_no_position(symbol, price)
            return
        
        # Log position status before sell attempt
        self.trade_logger.info(
            f"[SELL ATTEMPT] {symbol} | Total Vol: {position.volume} | "
            f"Available (can_use): {position.can_use_volume} | "
            f"Today Bought: {position.today_bought}"
        )
        
        # Attempt to sell available volume
        # OrderManager.sell() will enforce T+1 rules
        sell_volume = position.can_use_volume
        
        if sell_volume <= 0:
            # T+1 restriction - OrderManager will log this
            self.order_manager.sell(symbol, price, position.volume, "RSI_Strategy")
            return
        
        # Place sell order for available volume
        success, order_id = self.order_manager.sell(
            symbol=symbol,
            price=price,
            quantity=sell_volume,
            strategy_name="RSI_Strategy"
        )
        
        if success:
            rsi_str = f"{rsi_value:.2f}" if rsi_value is not None else "N/A"
            self.trade_logger.info(
                f"[SELL EXECUTED] {symbol} | Price: {price:.4f} | Vol: {sell_volume} | "
                f"RSI: {rsi_str} | OrderID: {order_id}"
            )

    def _health_check(self):
        """Periodic health check for connection status."""
        if not self.connected and self.running:
            self.trade_logger.warning("Connection lost. Attempting reconnection...")
            self._handle_disconnection()

    def stop(self):
        """Stop the trading engine gracefully."""
        self.trade_logger.info("Stopping Live Trading Engine...")
        self.running = False
        self.stop_event.set()
        
        # Stop strategy
        try:
            self.strategy.on_stop()
        except Exception as e:
            self.trade_logger.error(f"Error stopping strategy: {e}")
        
        # Disconnect trader
        if self.xt_trader:
            try:
                self.xt_trader.stop()
            except Exception as e:
                self.trade_logger.error(f"Error stopping trader: {e}")
        
        self.connected = False
        self.trade_logger.info("Live Trading Engine stopped.")

    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status.
        
        Returns:
            Dictionary with portfolio information
        """
        if self.order_manager is None:
            return {}
        
        asset = self.order_manager.get_asset()
        positions = self.order_manager.get_positions()
        
        status = {
            'cash': asset.cash if asset else 0,
            'market_value': asset.market_value if asset else 0,
            'total_asset': asset.total_asset if asset else 0,
            'positions': []
        }
        
        for p in positions:
            status['positions'].append({
                'symbol': p.stock_code,
                'volume': p.volume,
                'can_use_volume': p.can_use_volume,
                'today_bought': p.today_bought,
                'market_value': p.market_value,
                'cost_price': p.open_price
            })
        
        # Log status
        self.trade_logger.info(f"Portfolio: Cash={status['cash']:.2f}, MV={status['market_value']:.2f}")
        for pos in status['positions']:
            self.trade_logger.info(
                f"  {pos['symbol']}: Vol={pos['volume']}, Available={pos['can_use_volume']}, "
                f"TodayBought={pos['today_bought']}"
            )
        
        return status

    def run_single_check(self):
        """
        Run a single market data check and signal generation.
        Useful for scheduled/cron-based execution.
        """
        if not self.connected:
            if not self.connect():
                return
        
        self.trade_logger.info("Running single market check...")
        
        for symbol in self.symbols:
            try:
                # Get latest bar data
                data = xtdata.get_market_data(
                    field_list=['time', 'open', 'high', 'low', 'close', 'volume'],
                    stock_list=[symbol],
                    period=self.period,
                    count=1
                )
                
                if data:
                    self._on_market_data({symbol: data.get(symbol, [])})
                    
            except Exception as e:
                self.trade_logger.error(f"Error in single check for {symbol}: {e}")
