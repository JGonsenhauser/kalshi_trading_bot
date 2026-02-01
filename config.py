"""
Configuration Management for Kalshi Trading Bot
Centralized settings, validation, and environment loading
"""
import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration with validation"""
    
    # API Configuration
    KALSHI_API_KEY: str = os.getenv('KALSHI_API_KEY', '')
    KALSHI_API_SECRET: str = os.getenv('KALSHI_API_SECRET', '')
    KALSHI_ENV: Literal['demo', 'prod'] = os.getenv('KALSHI_ENV', 'demo')
    
    # API URLs
    KALSHI_BASE_URL: str = (
        'https://demo-api.kalshi.co/trade-api/v2' if KALSHI_ENV == 'demo'
        else 'https://trading-api.kalshi.com/trade-api/v2'
    )
    
    NEWS_API_KEY: str = os.getenv('NEWS_API_KEY', '')
    NEWS_API_URL: str = 'https://newsapi.org/v2/everything'
    
    # Risk Management
    INITIAL_BALANCE: float = float(os.getenv('INITIAL_BALANCE', '10000.0'))
    RISK_PER_TRADE_PCT: float = float(os.getenv('RISK_PER_TRADE_PCT', '0.01'))
    MAX_DAILY_DRAWDOWN_PCT: float = float(os.getenv('MAX_DAILY_DRAWDOWN_PCT', '0.05'))
    MAX_OPEN_POSITIONS: int = int(os.getenv('MAX_OPEN_POSITIONS', '5'))
    
    # Trading Parameters
    DEVIATION_THRESHOLD: float = float(os.getenv('DEVIATION_THRESHOLD', '0.05'))
    STOP_LOSS_DEVIATION: float = float(os.getenv('STOP_LOSS_DEVIATION', '0.05'))
    SCAN_INTERVAL_SECONDS: int = int(os.getenv('SCAN_INTERVAL_SECONDS', '30'))
    
    # External Sources
    POLL_AGGREGATOR_URL: str = os.getenv('POLL_AGGREGATOR_URL', 'https://www.realclearpolitics.com')
    ENABLE_NEWS_TRIGGERS: bool = os.getenv('ENABLE_NEWS_TRIGGERS', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'kalshi_bot.log')
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate critical configuration. Returns list of errors."""
        errors = []
        
        if not cls.KALSHI_API_KEY:
            errors.append("KALSHI_API_KEY not set")
        if not cls.KALSHI_API_SECRET:
            errors.append("KALSHI_API_SECRET not set")
        if cls.KALSHI_ENV not in ['demo', 'prod']:
            errors.append("KALSHI_ENV must be 'demo' or 'prod'")
        
        # Risk validation
        if cls.RISK_PER_TRADE_PCT <= 0 or cls.RISK_PER_TRADE_PCT > 0.1:
            errors.append("RISK_PER_TRADE_PCT should be 0-10%")
        if cls.MAX_DAILY_DRAWDOWN_PCT <= 0 or cls.MAX_DAILY_DRAWDOWN_PCT > 0.5:
            errors.append("MAX_DAILY_DRAWDOWN_PCT should be 0-50%")
        
        return errors
    
    @classmethod
    def is_sandbox(cls) -> bool:
        """Check if running in sandbox/demo mode"""
        return cls.KALSHI_ENV == 'demo'


# Category mappings for fair value routing
CATEGORY_MAPPINGS = {
    'Politics': ['politics', 'election', 'president', 'senate', 'congress'],
    'Economics': ['cpi', 'inflation', 'gdp', 'jobs', 'unemployment', 'fed'],
    'Sports': ['nfl', 'nba', 'mlb', 'f1', 'racing', 'soccer'],
    'Climate': ['temperature', 'weather', 'climate'],
}


def get_category(market_title: str) -> str:
    """Infer market category from title"""
    title_lower = market_title.lower()
    for category, keywords in CATEGORY_MAPPINGS.items():
        if any(kw in title_lower for kw in keywords):
            return category
    return 'Other'
