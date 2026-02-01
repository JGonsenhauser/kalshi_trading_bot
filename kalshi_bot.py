"""
Kalshi Trading Bot - Main Engine
Mimic @michaelbeer01's approach: Fast execution, edge detection, risk discipline

Core Loop:
1. Scan markets for mispricings (fair value vs implied odds)
2. Detect arbitrage across related markets
3. Execute trades with 1% position sizing
4. Monitor positions: Cut losers fast (5% edge flip), let winners run
5. Halt if daily drawdown >5% - PRESERVE CAPITAL
"""
import asyncio
import aiohttp
import logging
import colorlog
from typing import Optional, List, Dict
from datetime import datetime
import backoff
from aiolimiter import AsyncLimiter

from config import Config
from risk_manager import RiskManager
from fair_value import FairValueEngine

# Setup colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(getattr(logging, Config.LOG_LEVEL))

# File logging
file_handler = logging.FileHandler(Config.LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


class KalshiBot:
    """
    Main trading bot - Michael Beer's fast execution style
    - Async API calls for speed
    - Real-time edge detection
    - Disciplined risk management
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.risk_manager = RiskManager(
            initial_balance=Config.INITIAL_BALANCE,
            risk_per_trade_pct=Config.RISK_PER_TRADE_PCT,
            max_daily_dd_pct=Config.MAX_DAILY_DRAWDOWN_PCT,
            stop_loss_deviation=Config.STOP_LOSS_DEVIATION,
            max_positions=Config.MAX_OPEN_POSITIONS,
        )
        self.fair_value_engine = FairValueEngine()
        
        # Rate limiting: Kalshi allows ~10 req/s
        self.rate_limiter = AsyncLimiter(10, 1)  # 10 requests per second
        
        self.running = False
        self.loop_count = 0
    
    async def initialize(self):
        """Setup async session with auth"""
        headers = {
            'Authorization': f'Bearer {Config.KALSHI_API_KEY}',
            'Content-Type': 'application/json',
        }
        self.session = aiohttp.ClientSession(
            base_url=Config.KALSHI_BASE_URL,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self.fair_value_engine.initialize()
        logger.info(f"🤖 Kalshi Bot initialized in {'SANDBOX' if Config.is_sandbox() else 'LIVE'} mode")
    
    async def close(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        await self.fair_value_engine.close()
        logger.info("Bot shut down cleanly")
    
    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=3)
    async def _api_request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """
        Make rate-limited API request with retry logic
        Exponential backoff on failures - Beer's reliability focus
        """
        async with self.rate_limiter:
            try:
                async with self.session.request(method, endpoint, **kwargs) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 401:
                        logger.error("❌ Authentication failed - check API keys")
                        return None
                    else:
                        logger.warning(f"API {endpoint} returned {resp.status}: {await resp.text()}")
                        return None
            except asyncio.TimeoutError:
                logger.error(f"Timeout on {endpoint}")
                return None
    
    async def fetch_balance(self) -> float:
        """Get current account balance"""
        data = await self._api_request('GET', '/portfolio/balance')
        if data and 'balance' in data:
            balance = float(data['balance']) / 100  # Kalshi uses cents
            self.risk_manager.update_balance(balance)
            return balance
        return self.risk_manager.current_balance
    
    async def list_markets(self, status: str = 'open', limit: int = 100) -> List[dict]:
        """Fetch open markets - scan for opportunities"""
        data = await self._api_request('GET', '/markets', params={'status': status, 'limit': limit})
        if data and 'markets' in data:
            return data['markets']
        return []
    
    async def get_market_details(self, market_id: str) -> Optional[dict]:
        """Get detailed market data"""
        return await self._api_request('GET', f'/markets/{market_id}')
    
    async def place_order(self, market_id: str, side: str, count: int, order_type: str = 'market') -> bool:
        """
        Execute trade - fast like Beer's demos
        side: 'yes' or 'no'
        count: Number of contracts
        """
        payload = {
            'market_id': market_id,
            'side': side,
            'count': count,
            'type': order_type,  # 'market' for speed
        }
        
        data = await self._api_request('POST', '/orders', json=payload)
        
        if data and data.get('order'):
            logger.info(f"✅ ORDER FILLED: {market_id} {side} x{count}")
            return True
        else:
            logger.error(f"❌ ORDER FAILED: {market_id} {side} x{count}")
            return False
    
    async def scan_and_trade(self):
        """
        Main trading logic - Beer's edge hunting loop
        1. Fetch markets
        2. Calculate fair value for each
        3. Trigger if mispricing >5%
        4. Execute with 1% sizing
        """
        markets = await self.list_markets()
        if not markets:
            logger.warning("No markets fetched")
            return
        
        logger.debug(f"Scanning {len(markets)} markets...")
        
        # Detect arbitrage opportunities
        arb_opps = await self.fair_value_engine.detect_arbitrage(markets)
        for m1, m2, reason in arb_opps:
            logger.info(f"🎯 {reason}")
            # TODO: Execute arb trades (buy low, sell high simultaneously)
        
        # Scan for mispricings
        for market in markets:
            if self.risk_manager.halted:
                logger.warning("⏸️ Trading halted - skipping new positions")
                break
            
            # Skip if already have position
            if market['id'] in self.risk_manager.positions:
                continue
            
            # Check if can open new position
            can_open, reason = self.risk_manager.can_open_position()
            if not can_open:
                logger.debug(f"Position limit: {reason}")
                break
            
            try:
                # Calculate fair value
                fair_prob = await self.fair_value_engine.calculate_fair_value(market)
                
                # Extract market's implied probability
                yes_bid = market.get('yes_bid', 50) / 100.0
                yes_ask = market.get('yes_ask', 50) / 100.0
                implied_prob = (yes_bid + yes_ask) / 2.0
                
                # Calculate deviation (edge)
                deviation = abs(fair_prob - implied_prob)
                
                # Trigger trade if edge >5%
                if deviation >= Config.DEVIATION_THRESHOLD:
                    # Determine side: Buy underpriced, sell overpriced
                    side = 'yes' if fair_prob > implied_prob else 'no'
                    entry_price = yes_ask if side == 'yes' else (1 - yes_bid)
                    
                    # Calculate position size
                    size = self.risk_manager.calculate_position_size(entry_price, deviation)
                    
                    if size >= 1:
                        logger.info(
                            f"🔍 EDGE FOUND: {market['title'][:50]}... | "
                            f"Fair: {fair_prob:.2%} | Implied: {implied_prob:.2%} | "
                            f"Edge: {deviation:.2%} | Side: {side.upper()}"
                        )
                        
                        # Execute trade
                        if await self.place_order(market['id'], side, int(size)):
                            self.risk_manager.add_position(
                                market_id=market['id'],
                                side=side,
                                size=size,
                                entry_price=entry_price,
                                entry_fair_value=fair_prob,
                            )
            
            except Exception as e:
                logger.error(f"Error processing {market.get('title', 'unknown')}: {e}")
    
    async def monitor_positions(self):
        """
        PTJ Rule: Cut losers fast, let winners run
        Check all positions for:
        1. Edge deterioration (fair value shifted >5%)
        2. Execute exit if stop triggered
        """
        if not self.risk_manager.positions:
            return
        
        logger.debug(f"Monitoring {len(self.risk_manager.positions)} positions...")
        
        for market_id in list(self.risk_manager.positions.keys()):
            try:
                # Fetch latest market data
                market = await self.get_market_details(market_id)
                if not market:
                    continue
                
                # Recalculate fair value
                current_fair = await self.fair_value_engine.calculate_fair_value(market)
                
                # Get current market price
                yes_bid = market.get('yes_bid', 50) / 100.0
                yes_ask = market.get('yes_ask', 50) / 100.0
                current_price = (yes_bid + yes_ask) / 2.0
                
                # Update position
                self.risk_manager.update_position(market_id, current_price, current_fair)
                
                # Check if should cut
                should_cut, cut_reason = self.risk_manager.should_cut_position(market_id)
                
                if should_cut:
                    position = self.risk_manager.positions[market_id]
                    exit_side = 'no' if position.side == 'yes' else 'yes'  # Close opposite side
                    
                    logger.warning(f"🔪 CUTTING LOSER: {market['title'][:50]}... | {cut_reason}")
                    
                    if await self.place_order(market_id, exit_side, int(position.size)):
                        self.risk_manager.close_position(market_id, current_price, cut_reason)
                
            except Exception as e:
                logger.error(f"Error monitoring position {market_id}: {e}")
    
    async def run(self):
        """
        Main event loop - Beer's high-frequency approach
        Continuously scan → trade → monitor
        """
        logger.info("=" * 60)
        logger.info("🚀 KALSHI BOT STARTING - Michael Beer Style")
        logger.info(f"Environment: {'SANDBOX (Paper Trading)' if Config.is_sandbox() else '⚠️ LIVE TRADING'}")
        logger.info(f"Initial Balance: ${Config.INITIAL_BALANCE:,.2f}")
        logger.info(f"Risk per Trade: {Config.RISK_PER_TRADE_PCT:.1%}")
        logger.info(f"Max Daily Drawdown: {Config.MAX_DAILY_DRAWDOWN_PCT:.1%}")
        logger.info("=" * 60)
        
        # Validate config
        errors = Config.validate()
        if errors:
            logger.critical(f"❌ Configuration errors: {errors}")
            return
        
        await self.initialize()
        
        # Fetch initial balance
        await self.fetch_balance()
        
        self.running = True
        
        try:
            while self.running:
                self.loop_count += 1
                
                # Check daily drawdown halt
                if self.risk_manager.check_daily_drawdown():
                    logger.error("🛑 Daily drawdown limit reached - halting until reset")
                    await asyncio.sleep(3600)  # Wait 1 hour, check again
                    continue
                
                # Scan for opportunities
                await self.scan_and_trade()
                
                # Monitor existing positions
                await self.monitor_positions()
                
                # Portfolio summary every 10 loops
                if self.loop_count % 10 == 0:
                    await self.fetch_balance()
                    summary = self.risk_manager.get_portfolio_summary()
                    logger.info(
                        f"📊 PORTFOLIO | Balance: ${summary['balance']:,.2f} | "
                        f"Daily P&L: ${summary['daily_pnl']:+,.2f} ({summary['daily_pnl_pct']:+.2%}) | "
                        f"Positions: {summary['open_positions']} | "
                        f"Status: {'HALTED' if summary['halted'] else 'ACTIVE'}"
                    )
                
                # Sleep before next scan
                await asyncio.sleep(Config.SCAN_INTERVAL_SECONDS)
        
        except KeyboardInterrupt:
            logger.info("⏹️ Shutdown signal received")
        except Exception as e:
            logger.critical(f"💥 Fatal error: {e}", exc_info=True)
        finally:
            self.running = False
            await self.close()


async def main():
    """Entry point"""
    bot = KalshiBot()
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
