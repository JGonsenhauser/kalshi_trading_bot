#!/usr/bin/env python3
"""Quick test of the dashboard feature"""

import sys
import asyncio
from datetime import datetime
from kalshi_bot import KalshiBot
from risk_manager import Position

async def test():
    # Create bot
    bot = KalshiBot()
    
    # Manually create some positions for testing
    pos1 = Position(
        market_id='TEST1',
        side='yes',
        size=5,
        entry_price=0.45,
        entry_fair_value=0.55,
        timestamp=datetime.now()
    )
    pos1.update(current_price=0.48, current_fair_value=0.52)
    
    pos2 = Position(
        market_id='TEST2',
        side='no',
        size=3,
        entry_price=0.60,
        entry_fair_value=0.55,
        timestamp=datetime.now()
    )
    pos2.update(current_price=0.58, current_fair_value=0.54)
    
    bot.risk_manager.positions = {
        'TEST1': pos1,
        'TEST2': pos2
    }
    
    # Print the dashboard
    print("Testing print_portfolio_dashboard()...")
    bot.print_portfolio_dashboard()
    print("\n✅ Dashboard test completed successfully!")

if __name__ == '__main__':
    asyncio.run(test())
