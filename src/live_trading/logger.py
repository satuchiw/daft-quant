"""
Trade Logger Module for Live Trading.
Provides comprehensive logging for all trading events.
"""

import logging
import sys
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class EventType(Enum):
    """Enumeration of trading event types."""
    SIGNAL = "SIGNAL"
    ORDER_PLACED = "ORDER_PLACED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_FAILED = "ORDER_FAILED"
    POSITION_UPDATE = "POSITION_UPDATE"
    T1_RESTRICTION = "T1_RESTRICTION"
    CONNECTION = "CONNECTION"
    DATA_RECEIVED = "DATA_RECEIVED"
    ERROR = "ERROR"
    INFO = "INFO"


@dataclass
class TradeEvent:
    """Data class representing a trading event."""
    timestamp: str
    event_type: str
    symbol: str
    signal_type: str
    price: float
    volume: int
    order_id: str
    status: str
    message: str
    rsi_value: Optional[float] = None
    can_use_volume: Optional[int] = None
    total_volume: Optional[int] = None


class TradeLogger:
    """
    Comprehensive trade logger for live trading.
    Logs events to both file and console, with optional CSV export.
    
    Log Format: [Time, Event Type, Symbol, Signal Type, Price, Volume, OrderID, Status, Message]
    """
    
    def __init__(
        self,
        name: str = "TradeLogger",
        log_file: str = "live_trading.log",
        csv_file: Optional[str] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize TradeLogger.
        
        Args:
            name: Logger name
            log_file: Path to log file
            csv_file: Optional path to CSV file for structured trade logs
            log_level: Logging level
        """
        self.name = name
        self.log_file = log_file
        self.csv_file = csv_file or log_file.replace('.log', '_trades.csv')
        
        # Setup standard logger
        self.logger = self._setup_logger(name, log_file, log_level)
        
        # Initialize CSV file with headers
        self._init_csv()
    
    def _setup_logger(self, name: str, log_file: str, log_level: int) -> logging.Logger:
        """Setup the standard Python logger."""
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        if logger.handlers:
            logger.handlers.clear()
        
        # File Handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'EventType', 'Symbol', 'SignalType', 
                    'Price', 'Volume', 'OrderID', 'Status', 'Message',
                    'RSI', 'CanUseVolume', 'TotalVolume'
                ])
    
    def _write_csv(self, event: TradeEvent):
        """Write event to CSV file."""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    event.timestamp, event.event_type, event.symbol,
                    event.signal_type, event.price, event.volume,
                    event.order_id, event.status, event.message,
                    event.rsi_value, event.can_use_volume, event.total_volume
                ])
        except Exception as e:
            self.logger.error(f"Failed to write to CSV: {e}")
    
    def _create_event(
        self,
        event_type: EventType,
        symbol: str = "",
        signal_type: str = "",
        price: float = 0.0,
        volume: int = 0,
        order_id: str = "",
        status: str = "",
        message: str = "",
        rsi_value: Optional[float] = None,
        can_use_volume: Optional[int] = None,
        total_volume: Optional[int] = None
    ) -> TradeEvent:
        """Create a TradeEvent instance."""
        return TradeEvent(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            event_type=event_type.value,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            volume=volume,
            order_id=order_id,
            status=status,
            message=message,
            rsi_value=rsi_value,
            can_use_volume=can_use_volume,
            total_volume=total_volume
        )
    
    def log_signal(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        rsi_value: Optional[float] = None,
        message: str = ""
    ):
        """Log a trading signal."""
        event = self._create_event(
            EventType.SIGNAL,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            rsi_value=rsi_value,
            status="GENERATED",
            message=message or f"Signal generated: {signal_type}"
        )
        rsi_str = f"{rsi_value:.2f}" if rsi_value is not None else "N/A"
        self.logger.info(
            f"[SIGNAL] {symbol} | {signal_type.upper()} @ {price:.4f} | RSI: {rsi_str}"
        )
        self._write_csv(event)
    
    def log_order_placed(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        volume: int,
        order_id: str,
        message: str = ""
    ):
        """Log an order placement."""
        event = self._create_event(
            EventType.ORDER_PLACED,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            volume=volume,
            order_id=order_id,
            status="PLACED",
            message=message or f"Order placed successfully"
        )
        self.logger.info(
            f"[ORDER_PLACED] {symbol} | {signal_type.upper()} | "
            f"Price: {price:.4f} | Vol: {volume} | OrderID: {order_id}"
        )
        self._write_csv(event)
    
    def log_order_filled(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        volume: int,
        order_id: str,
        message: str = ""
    ):
        """Log an order fill."""
        event = self._create_event(
            EventType.ORDER_FILLED,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            volume=volume,
            order_id=order_id,
            status="FILLED",
            message=message or f"Order filled"
        )
        self.logger.info(
            f"[ORDER_FILLED] {symbol} | {signal_type.upper()} | "
            f"Price: {price:.4f} | Vol: {volume} | OrderID: {order_id}"
        )
        self._write_csv(event)
    
    def log_order_failed(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        volume: int,
        order_id: str = "",
        message: str = ""
    ):
        """Log an order failure."""
        event = self._create_event(
            EventType.ORDER_FAILED,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            volume=volume,
            order_id=order_id,
            status="FAILED",
            message=message
        )
        self.logger.error(
            f"[ORDER_FAILED] {symbol} | {signal_type.upper()} | "
            f"Price: {price:.4f} | Vol: {volume} | Reason: {message}"
        )
        self._write_csv(event)
    
    def log_t1_restriction(
        self,
        symbol: str,
        price: float,
        total_volume: int,
        can_use_volume: int,
        message: str = ""
    ):
        """Log T+1 restriction event (sell signal ignored)."""
        event = self._create_event(
            EventType.T1_RESTRICTION,
            symbol=symbol,
            signal_type="SELL",
            price=price,
            volume=0,
            status="IGNORED",
            message=message or f"Sell signal ignored: T+1 restriction. can_use_volume={can_use_volume}",
            can_use_volume=can_use_volume,
            total_volume=total_volume
        )
        self.logger.warning(
            f"[T+1 RESTRICTION] {symbol} | SELL signal IGNORED | "
            f"Total Vol: {total_volume} | Available (can_use): {can_use_volume} | "
            f"Reason: Shares bought today cannot be sold until tomorrow"
        )
        self._write_csv(event)
    
    def log_insufficient_cash(
        self,
        symbol: str,
        price: float,
        volume: int,
        required: float,
        available: float
    ):
        """Log insufficient cash for buy order."""
        event = self._create_event(
            EventType.ORDER_FAILED,
            symbol=symbol,
            signal_type="BUY",
            price=price,
            volume=volume,
            status="REJECTED",
            message=f"Insufficient cash. Required: {required:.2f}, Available: {available:.2f}"
        )
        self.logger.warning(
            f"[INSUFFICIENT_CASH] {symbol} | BUY signal REJECTED | "
            f"Required: {required:.2f} | Available: {available:.2f}"
        )
        self._write_csv(event)
    
    def log_no_position(self, symbol: str, price: float):
        """Log sell signal with no position."""
        event = self._create_event(
            EventType.ORDER_FAILED,
            symbol=symbol,
            signal_type="SELL",
            price=price,
            status="REJECTED",
            message="No position to sell"
        )
        self.logger.warning(f"[NO_POSITION] {symbol} | SELL signal REJECTED | No position held")
        self._write_csv(event)
    
    def log_connection(self, status: str, message: str = ""):
        """Log connection events."""
        event = self._create_event(
            EventType.CONNECTION,
            status=status,
            message=message
        )
        level = logging.INFO if status == "CONNECTED" else logging.WARNING
        self.logger.log(level, f"[CONNECTION] Status: {status} | {message}")
        self._write_csv(event)
    
    def log_data_received(self, symbol: str, bar_time: str, ohlcv: Dict[str, float]):
        """Log market data received."""
        self.logger.debug(
            f"[DATA] {symbol} @ {bar_time} | "
            f"O:{ohlcv.get('open', 0):.4f} H:{ohlcv.get('high', 0):.4f} "
            f"L:{ohlcv.get('low', 0):.4f} C:{ohlcv.get('close', 0):.4f} V:{ohlcv.get('volume', 0):.0f}"
        )
    
    def log_position_update(
        self,
        symbol: str,
        total_volume: int,
        can_use_volume: int,
        market_value: float,
        cost_price: float
    ):
        """Log position update."""
        event = self._create_event(
            EventType.POSITION_UPDATE,
            symbol=symbol,
            volume=total_volume,
            can_use_volume=can_use_volume,
            total_volume=total_volume,
            message=f"Position update: MV={market_value:.2f}, Cost={cost_price:.4f}"
        )
        self.logger.info(
            f"[POSITION] {symbol} | Total: {total_volume} | Available: {can_use_volume} | "
            f"MV: {market_value:.2f} | Cost: {cost_price:.4f}"
        )
        self._write_csv(event)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)


def setup_logger(name: str = "LiveTrading", log_file: str = "live_trading.log") -> logging.Logger:
    """
    Legacy function for backward compatibility.
    Returns a standard Python logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
