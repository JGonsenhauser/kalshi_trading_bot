"""
Risk Management System - Preserve Capital Edition
Implements position sizing, stop losses, drawdown limits, and PTJ-style risk controls
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Position:
    """Track individual position state"""
    def __init__(self, market_id: str, side: str, size: float, entry_price: float, 
                 entry_fair_value: float, timestamp: datetime):
        self.market_id = market_id
        self.side = side  # 'yes' or 'no'
        self.size = size  # Contract count
        self.entry_price = entry_price
        self.entry_fair_value = entry_fair_value
        self.timestamp = timestamp
        self.current_price: Optional[float] = None
        self.current_fair_value: Optional[float] = None
    
    def update(self, current_price: float, current_fair_value: float):
        """Update position with latest market data"""
        self.current_price = current_price
        self.current_fair_value = current_fair_value
    
    def pnl(self) -> float:
        """Calculate unrealized P&L"""
        if self.current_price is None:
            return 0.0
        price_diff = self.current_price - self.entry_price
        multiplier = 1 if self.side == 'yes' else -1
        return multiplier * price_diff * self.size
    
    def edge_deterioration(self) -> float:
        """Calculate how much edge has eroded (positive = edge lost)"""
        if self.current_fair_value is None:
            return 0.0
        return abs(self.current_fair_value - self.entry_fair_value)


class RiskManager:
    """
    Core risk management - Michael Beer's discipline:
    - 1% per trade max
    - Cut losers fast (5% edge flip)
    - Let winners run (no early exits)
    - 5% daily drawdown halt
    """
    
    def __init__(self, initial_balance: float, risk_per_trade_pct: float = 0.01,
                 max_daily_dd_pct: float = 0.05, stop_loss_deviation: float = 0.05,
                 max_positions: int = 5):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.peak_balance = initial_balance
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_daily_dd_pct = max_daily_dd_pct
        self.stop_loss_deviation = stop_loss_deviation
        self.max_positions = max_positions
        
        self.positions: Dict[str, Position] = {}
        self.daily_start_balance = initial_balance
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0)
        self.halted = False
        self.halt_reason: Optional[str] = None
    
    def update_balance(self, new_balance: float):
        """Update current balance and track peak"""
        self.current_balance = new_balance
        self.peak_balance = max(self.peak_balance, new_balance)
        self._check_daily_reset()
    
    def _check_daily_reset(self):
        """Reset daily tracking at midnight"""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_start_balance = self.current_balance
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0)
            if self.halt_reason == 'daily_drawdown':
                logger.info("Daily reset - resuming trading")
                self.halted = False
                self.halt_reason = None
    
    def check_daily_drawdown(self) -> bool:
        """Check if daily drawdown limit breached - PRESERVE CAPITAL"""
        daily_pnl = self.current_balance - self.daily_start_balance
        daily_dd_pct = daily_pnl / self.daily_start_balance
        
        if daily_dd_pct <= -self.max_daily_dd_pct:
            if not self.halted:
                self.halted = True
                self.halt_reason = 'daily_drawdown'
                logger.error(f"🛑 DAILY DRAWDOWN HALT: {daily_dd_pct:.2%} - Preserving capital")
            return True
        return False
    
    def calculate_position_size(self, market_price: float, edge_deviation: float, 
                                balance_override: Optional[float] = None) -> float:
        """
        Calculate position size using risk-based approach
        Size = (Balance * RiskPct) / Price, scaled by edge strength
        """
        balance = balance_override or self.current_balance
        if balance <= 0 or market_price <= 0:
            return 0.0
        
        # Base risk allocation
        risk_amount = balance * self.risk_per_trade_pct
        
        # Scale by edge strength (stronger edge = larger size, up to max)
        edge_multiplier = min(edge_deviation / self.stop_loss_deviation, 1.5)
        adjusted_risk = risk_amount * edge_multiplier
        
        # Convert to contract count
        size = adjusted_risk / market_price
        return max(1.0, round(size))  # Minimum 1 contract
    
    def can_open_position(self) -> tuple[bool, Optional[str]]:
        """Check if new position allowed"""
        if self.halted:
            return False, f"Trading halted: {self.halt_reason}"
        
        if len(self.positions) >= self.max_positions:
            return False, f"Max positions reached ({self.max_positions})"
        
        if self.current_balance < self.initial_balance * 0.5:
            return False, "Balance below 50% of initial - risk limit"
        
        return True, None
    
    def add_position(self, market_id: str, side: str, size: float, entry_price: float,
                     entry_fair_value: float) -> bool:
        """Register new position"""
        can_open, reason = self.can_open_position()
        if not can_open:
            logger.warning(f"Position rejected: {reason}")
            return False
        
        position = Position(
            market_id=market_id,
            side=side,
            size=size,
            entry_price=entry_price,
            entry_fair_value=entry_fair_value,
            timestamp=datetime.now()
        )
        self.positions[market_id] = position
        logger.info(f"✅ Position opened: {market_id} {side} x{size} @ {entry_price}")
        return True
    
    def update_position(self, market_id: str, current_price: float, current_fair_value: float):
        """Update position with latest data"""
        if market_id in self.positions:
            self.positions[market_id].update(current_price, current_fair_value)
    
    def should_cut_position(self, market_id: str) -> tuple[bool, Optional[str]]:
        """
        PTJ Rule: Cut losers fast if edge evaporates
        Check if fair value shifted against us by stop_loss_deviation
        """
        if market_id not in self.positions:
            return False, None
        
        position = self.positions[market_id]
        edge_loss = position.edge_deterioration()
        
        if edge_loss >= self.stop_loss_deviation:
            return True, f"Edge flip: {edge_loss:.2%} (stop at {self.stop_loss_deviation:.2%})"
        
        # Additional safety: Hard stop if losing >10% on position
        pnl = position.pnl()
        loss_pct = pnl / (position.entry_price * position.size)
        if loss_pct < -0.10:
            return True, f"Hard stop: {loss_pct:.2%} loss"
        
        return False, None
    
    def close_position(self, market_id: str, exit_price: float, reason: str = "manual"):
        """Close position and update balance"""
        if market_id not in self.positions:
            logger.warning(f"Cannot close non-existent position: {market_id}")
            return
        
        position = self.positions[market_id]
        position.update(exit_price, position.current_fair_value or position.entry_fair_value)
        pnl = position.pnl()
        
        self.current_balance += pnl
        logger.info(f"🔒 Position closed: {market_id} | P&L: ${pnl:.2f} | Reason: {reason}")
        
        del self.positions[market_id]
        self._check_daily_reset()
        self.check_daily_drawdown()
    
    def get_portfolio_summary(self) -> dict:
        """Get current portfolio state"""
        total_pnl = sum(pos.pnl() for pos in self.positions.values())
        daily_pnl = self.current_balance - self.daily_start_balance
        
        return {
            'balance': self.current_balance,
            'peak_balance': self.peak_balance,
            'total_drawdown_pct': (self.current_balance - self.peak_balance) / self.peak_balance,
            'daily_pnl': daily_pnl,
            'daily_pnl_pct': daily_pnl / self.daily_start_balance,
            'open_positions': len(self.positions),
            'unrealized_pnl': total_pnl,
            'halted': self.halted,
            'halt_reason': self.halt_reason,
        }
