"""
Order Manager Module for Live Trading.
Handles order placement with T+1 settlement enforcement for Chinese A-shares.
"""

from typing import Dict, Optional, List, Tuple, Union
from dataclasses import dataclass
import time

# Import xtquant
try:
    from xtquant import xttrader, xttype, xtconstant
    XTQUANT_AVAILABLE = True
except ImportError:
    print("Warning: xtquant not found. Running in mock mode.")
    XTQUANT_AVAILABLE = False

from .logger import TradeLogger


@dataclass
class PositionInfo:
    """Position information with T+1 details."""
    stock_code: str
    volume: int              # Total volume held
    can_use_volume: int      # Available volume for selling (T+1 compliant)
    frozen_volume: int       # Frozen volume (bought today, cannot sell)
    open_price: float        # Average cost price
    market_value: float      # Current market value
    
    @property
    def today_bought(self) -> int:
        """Volume bought today (cannot be sold due to T+1)."""
        return self.volume - self.can_use_volume


class OrderManager:
    """
    Order Manager with T+1 Settlement Enforcement.
    
    CRITICAL: For Chinese A-share market, stocks bought today cannot be sold
    until the next trading day (T+1 rule). This manager strictly enforces this
    by checking `can_use_volume` before any sell order.
    """
    
    def __init__(
        self,
        xt_trader,
        account_id: str,
        trade_logger: TradeLogger,
        min_order_volume: int = 100
    ):
        """
        Initialize OrderManager.
        
        Args:
            xt_trader: XtQuantTrader instance
            account_id: Trading account ID
            trade_logger: TradeLogger instance for comprehensive logging
            min_order_volume: Minimum order volume (default 100 for A-shares)
        """
        self.xt_trader = xt_trader
        self.account_id = account_id
        self.logger = trade_logger
        self.min_order_volume = min_order_volume
        
        if XTQUANT_AVAILABLE:
            self.acc = xttype.StockAccount(account_id)
        else:
            self.acc = None
        
        # Track pending orders
        self.pending_orders: Dict[str, Dict] = {}
    
    def buy(
        self,
        symbol: str,
        price: float,
        quantity: int,
        strategy_name: str = "RSI_Strategy"
    ) -> Tuple[bool, str]:
        """
        Place a buy order.
        
        Args:
            symbol: Stock code (e.g. '510300.SH')
            price: Limit price
            quantity: Number of shares (must be multiple of 100 for A-share)
        
        Returns:
            Tuple of (success: bool, order_id: str)
        """
        # Validate quantity
        if quantity <= 0:
            self.logger.log_order_failed(
                symbol, "BUY", price, quantity,
                message="Invalid quantity: must be positive"
            )
            return False, ""
        
        # Round down to nearest 100 (A-share lot size)
        quantity = (quantity // self.min_order_volume) * self.min_order_volume
        if quantity < self.min_order_volume:
            self.logger.log_order_failed(
                symbol, "BUY", price, quantity,
                message=f"Quantity below minimum lot size ({self.min_order_volume})"
            )
            return False, ""
        
        # Check available cash
        asset = self.get_asset()
        if asset:
            required_cash = price * quantity * 1.0003  # Include commission estimate
            if asset.cash < required_cash:
                self.logger.log_insufficient_cash(
                    symbol, price, quantity, required_cash, asset.cash
                )
                return False, ""
        
        # Place order
        return self._place_order(symbol, price, quantity, "BUY", strategy_name)
    
    def sell(
        self,
        symbol: str,
        price: float,
        quantity: int,
        strategy_name: str = "RSI_Strategy"
    ) -> Tuple[bool, str]:
        """
        Place a sell order with T+1 enforcement.
        
        CRITICAL: This method enforces T+1 rules by checking can_use_volume.
        
        Args:
            symbol: Stock code
            price: Limit price
            quantity: Number of shares to sell
        
        Returns:
            Tuple of (success: bool, order_id: str)
        """
        # Get position with T+1 info
        position = self.get_position(symbol)
        
        if position is None:
            self.logger.log_no_position(symbol, price)
            return False, ""
        
        # ========== T+1 ENFORCEMENT ==========
        # CRITICAL: Use can_use_volume, NOT total volume
        available_volume = position.can_use_volume
        total_volume = position.volume
        
        if available_volume <= 0:
            # T+1 restriction: shares bought today cannot be sold
            self.logger.log_t1_restriction(
                symbol=symbol,
                price=price,
                total_volume=total_volume,
                can_use_volume=available_volume,
                message=f"All {total_volume} shares were bought today. T+1 rule prevents selling."
            )
            return False, ""
        
        # Adjust quantity to available volume
        if quantity > available_volume:
            self.logger.warning(
                f"Requested sell quantity ({quantity}) exceeds available volume ({available_volume}). "
                f"Adjusting to {available_volume}."
            )
            quantity = available_volume
        
        # Round down to lot size
        quantity = (quantity // self.min_order_volume) * self.min_order_volume
        if quantity < self.min_order_volume:
            self.logger.log_order_failed(
                symbol, "SELL", price, quantity,
                message=f"Available volume ({available_volume}) below minimum lot size"
            )
            return False, ""
        
        # Place order
        return self._place_order(symbol, price, quantity, "SELL", strategy_name)
    
    def _place_order(
        self,
        symbol: str,
        price: float,
        quantity: int,
        side: str,
        strategy_name: str
    ) -> Tuple[bool, str]:
        """
        Internal method to place order via xt_trader.
        
        Returns:
            Tuple of (success: bool, order_id: str)
        """
        if not XTQUANT_AVAILABLE or self.xt_trader is None:
            self.logger.error("xtquant not available. Cannot place order.")
            return False, ""
        
        try:
            order_type = xtconstant.STOCK_BUY if side == "BUY" else xtconstant.STOCK_SELL
            
            # Place order asynchronously
            order_id = self.xt_trader.order_stock_async(
                self.acc,
                symbol,
                order_type,
                quantity,
                xtconstant.FIX_PRICE,  # Limit order
                price,
                strategy_name,
                strategy_name
            )
            
            if order_id:
                self.logger.log_order_placed(
                    symbol=symbol,
                    signal_type=side,
                    price=price,
                    volume=quantity,
                    order_id=str(order_id)
                )
                
                # Track pending order
                self.pending_orders[str(order_id)] = {
                    'symbol': symbol,
                    'side': side,
                    'price': price,
                    'quantity': quantity,
                    'time': time.time()
                }
                
                return True, str(order_id)
            else:
                self.logger.log_order_failed(
                    symbol, side, price, quantity,
                    message="Order rejected by broker (no order_id returned)"
                )
                return False, ""
                
        except Exception as e:
            self.logger.log_order_failed(
                symbol, side, price, quantity,
                message=f"Exception during order placement: {str(e)}"
            )
            return False, ""
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        if not XTQUANT_AVAILABLE or self.xt_trader is None:
            return False
        
        try:
            self.xt_trader.cancel_order_stock_async(self.acc, int(order_id))
            self.logger.info(f"Cancel request sent for order: {order_id}")
            
            if order_id in self.pending_orders:
                del self.pending_orders[order_id]
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """
        Get position for a specific symbol with T+1 details.
        
        Returns:
            PositionInfo with can_use_volume for T+1 compliance, or None if no position
        """
        positions = self.get_positions()
        
        for pos in positions:
            if pos.stock_code == symbol:
                return pos
        
        return None
    
    def get_positions(self) -> List[PositionInfo]:
        """
        Get all positions with T+1 details.
        
        Returns:
            List of PositionInfo objects
        """
        if not XTQUANT_AVAILABLE or self.xt_trader is None:
            return []
        
        try:
            raw_positions = self.xt_trader.query_stock_positions(self.acc)
            
            positions = []
            for p in raw_positions:
                # Extract T+1 relevant fields from xtquant position object
                # Key field: can_use_volume - this is what we can actually sell
                pos_info = PositionInfo(
                    stock_code=p.stock_code,
                    volume=p.volume,
                    can_use_volume=p.can_use_volume,  # CRITICAL for T+1
                    frozen_volume=p.frozen_volume if hasattr(p, 'frozen_volume') else 0,
                    open_price=p.open_price if hasattr(p, 'open_price') else 0.0,
                    market_value=p.market_value if hasattr(p, 'market_value') else 0.0
                )
                positions.append(pos_info)
                
                # Log position with T+1 info
                self.logger.log_position_update(
                    symbol=pos_info.stock_code,
                    total_volume=pos_info.volume,
                    can_use_volume=pos_info.can_use_volume,
                    market_value=pos_info.market_value,
                    cost_price=pos_info.open_price
                )
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to query positions: {e}")
            return []
    
    def get_asset(self):
        """
        Get account assets (Cash, Market Value).
        
        Returns:
            Asset object with cash, market_value, total_asset attributes
        """
        if not XTQUANT_AVAILABLE or self.xt_trader is None:
            return None
        
        try:
            return self.xt_trader.query_stock_asset(self.acc)
        except Exception as e:
            self.logger.error(f"Failed to query asset: {e}")
            return None
    
    def get_available_cash(self) -> float:
        """Get available cash for trading."""
        asset = self.get_asset()
        return asset.cash if asset else 0.0
    
    def check_t1_sellable(self, symbol: str) -> Tuple[bool, int, int]:
        """
        Check if a symbol can be sold under T+1 rules.
        
        Returns:
            Tuple of (can_sell: bool, can_use_volume: int, total_volume: int)
        """
        position = self.get_position(symbol)
        
        if position is None:
            return False, 0, 0
        
        can_sell = position.can_use_volume > 0
        return can_sell, position.can_use_volume, position.volume
