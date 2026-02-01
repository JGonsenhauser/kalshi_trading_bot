"""
Simple test script to verify Kalshi API connection
Tests authentication and basic API calls without placing orders
"""
import asyncio
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()

KALSHI_API_KEY = os.getenv('KALSHI_API_KEY')
KALSHI_ENV = os.getenv('KALSHI_ENV', 'demo')
KALSHI_BASE_URL = (
    'https://demo-api.kalshi.co/trade-api/v2' if KALSHI_ENV == 'demo'
    else 'https://trading-api.kalshi.com/trade-api/v2'
)


async def test_connection():
    """Test API connection and authentication"""
    print("=" * 60)
    print("🔌 Testing Kalshi API Connection")
    print(f"Environment: {KALSHI_ENV.upper()}")
    print(f"URL: {KALSHI_BASE_URL}")
    print("=" * 60)
    print()
    
    headers = {
        'Authorization': f'Bearer {KALSHI_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    async with aiohttp.ClientSession(headers=headers, base_url=KALSHI_BASE_URL) as session:
        # Test 1: Fetch balance
        print("Test 1: Fetching account balance...")
        try:
            async with session.get('/portfolio/balance') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    balance = data.get('balance', 0) / 100  # Convert cents to dollars
                    print(f"✅ Balance: ${balance:,.2f}")
                elif resp.status == 401:
                    print("❌ Authentication failed - check API key")
                    return False
                else:
                    print(f"⚠️ Unexpected status: {resp.status}")
                    print(await resp.text())
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        print()
        
        # Test 2: Fetch markets
        print("Test 2: Fetching open markets...")
        try:
            async with session.get('/markets', params={'status': 'open', 'limit': 5}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    markets = data.get('markets', [])
                    print(f"✅ Found {len(markets)} markets")
                    
                    if markets:
                        print("\nSample markets:")
                        for i, market in enumerate(markets[:3], 1):
                            title = market.get('title', 'Unknown')
                            yes_bid = market.get('yes_bid', 0) / 100
                            yes_ask = market.get('yes_ask', 0) / 100
                            print(f"  {i}. {title[:60]}")
                            print(f"     Bid: {yes_bid:.2%} | Ask: {yes_ask:.2%}")
                else:
                    print(f"⚠️ Status: {resp.status}")
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        print()
        print("=" * 60)
        print("✅ API connection successful!")
        print("You're ready to run the bot.")
        print("=" * 60)
        return True


if __name__ == '__main__':
    success = asyncio.run(test_connection())
    if not success:
        print("\n⚠️ Fix errors above before running the bot")
        exit(1)
