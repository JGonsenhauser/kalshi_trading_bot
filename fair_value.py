"""
Fair Value Models - Edge Detection Engine
Compute "true" probability vs Kalshi's implied odds to find mispricings
Supports: Politics (poll aggregation), Economics (news-based), Arbitrage detection
"""
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import re
from bs4 import BeautifulSoup

from config import Config, get_category

logger = logging.getLogger(__name__)


class FairValueEngine:
    """Calculate fair value probabilities for different market types"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.news_cache: Dict[str, List[dict]] = {}
        self.poll_cache: Dict[str, float] = {}
    
    async def initialize(self):
        """Initialize async session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Cleanup"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def calculate_fair_value(self, market: dict) -> float:
        """
        Route to appropriate fair value model based on market category
        Returns probability (0.0-1.0)
        """
        await self.initialize()
        
        title = market.get('title', '')
        subtitle = market.get('subtitle', '')
        full_text = f"{title} {subtitle}".lower()
        
        category = get_category(title)
        
        try:
            if category == 'Politics':
                return await self._calculate_politics_fair_value(full_text, market)
            elif category == 'Economics':
                return await self._calculate_economics_fair_value(full_text, market)
            elif category == 'Sports':
                return await self._calculate_sports_fair_value(full_text, market)
            else:
                # Fallback: Use market's own pricing as baseline
                return self._extract_market_probability(market)
        except Exception as e:
            logger.error(f"Fair value calc failed for {title}: {e}")
            return self._extract_market_probability(market)
    
    def _extract_market_probability(self, market: dict) -> float:
        """Extract implied probability from Kalshi market prices"""
        yes_bid = market.get('yes_bid', 50)
        yes_ask = market.get('yes_ask', 50)
        # Mid-price as probability
        return (yes_bid + yes_ask) / 200.0
    
    async def _calculate_politics_fair_value(self, query: str, market: dict) -> float:
        """
        Politics: Aggregate polling data
        Strategy: Scrape RCP/538, average recent polls, adjust for house effects
        """
        # Extract candidate/proposition from query
        candidate = self._extract_candidate_name(query)
        if not candidate:
            logger.warning(f"No candidate found in: {query}")
            return self._extract_market_probability(market)
        
        # Check cache
        cache_key = f"poll_{candidate}"
        if cache_key in self.poll_cache:
            return self.poll_cache[cache_key]
        
        # Scrape polls (simplified - would use RCP/538 APIs in production)
        polls = await self._scrape_polls(candidate)
        
        if not polls:
            logger.info(f"No polls found for {candidate}, using market price")
            return self._extract_market_probability(market)
        
        # Average recent polls (simple model - could weight by recency/quality)
        fair_value = sum(polls) / len(polls)
        self.poll_cache[cache_key] = fair_value
        
        logger.debug(f"Politics fair value for {candidate}: {fair_value:.3f} (from {len(polls)} polls)")
        return fair_value
    
    def _extract_candidate_name(self, text: str) -> Optional[str]:
        """Extract candidate/party name from market text"""
        # Simple regex - expand for production
        patterns = [
            r'(trump|biden|harris|desantis|haley)',
            r'(republican|democrat|gop)',
            r'(yes|no)\s+win',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        return None
    
    async def _scrape_polls(self, candidate: str) -> List[float]:
        """
        Scrape polling data (STUB - implement with real sources)
        In production: Use RCP API, 538 data, or Selenium for dynamic content
        """
        # STUB: Return simulated polls for demo
        # TODO: Implement real scraping with BeautifulSoup/Selenium
        # Example targets:
        # - https://www.realclearpolitics.com/epolls/latest_polls/
        # - https://projects.fivethirtyeight.com/polls/
        
        logger.debug(f"[STUB] Scraping polls for {candidate}")
        
        # Simulate polls (replace with real scraping)
        if 'trump' in candidate.lower():
            return [0.48, 0.52, 0.50, 0.49]  # Example poll results
        elif 'biden' in candidate.lower():
            return [0.46, 0.44, 0.48, 0.47]
        else:
            return []  # No data
    
    async def _calculate_economics_fair_value(self, query: str, market: dict) -> float:
        """
        Economics: News sentiment + consensus forecasts
        Strategy: Check NewsAPI for CPI/jobs/Fed announcements, parse analyst expectations
        """
        # Extract economic indicator
        indicator = self._extract_economic_indicator(query)
        if not indicator:
            return self._extract_market_probability(market)
        
        # Fetch news
        news_articles = await self._fetch_news(indicator)
        
        if not news_articles:
            return self._extract_market_probability(market)
        
        # Parse consensus (STUB - would use NLP/regex to extract forecasts)
        consensus_prob = self._parse_economic_consensus(news_articles, query)
        
        logger.debug(f"Economics fair value for {indicator}: {consensus_prob:.3f}")
        return consensus_prob
    
    def _extract_economic_indicator(self, text: str) -> Optional[str]:
        """Identify economic indicator from market text"""
        indicators = {
            'cpi': ['cpi', 'inflation', 'consumer price'],
            'jobs': ['jobs', 'unemployment', 'nonfarm', 'payroll'],
            'gdp': ['gdp', 'growth', 'recession'],
            'fed': ['fed', 'federal reserve', 'rate', 'fomc'],
        }
        for key, keywords in indicators.items():
            if any(kw in text for kw in keywords):
                return key
        return None
    
    async def _fetch_news(self, query: str, max_articles: int = 10) -> List[dict]:
        """Fetch news from NewsAPI"""
        if not Config.NEWS_API_KEY or not Config.ENABLE_NEWS_TRIGGERS:
            return []
        
        cache_key = f"news_{query}"
        if cache_key in self.news_cache:
            return self.news_cache[cache_key]
        
        try:
            params = {
                'q': query,
                'apiKey': Config.NEWS_API_KEY,
                'pageSize': max_articles,
                'language': 'en',
                'sortBy': 'publishedAt',
            }
            async with self.session.get(Config.NEWS_API_URL, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    articles = data.get('articles', [])
                    self.news_cache[cache_key] = articles
                    return articles
                else:
                    logger.warning(f"NewsAPI returned {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"News fetch failed: {e}")
            return []
    
    def _parse_economic_consensus(self, articles: List[dict], query: str) -> float:
        """
        Parse consensus forecast from news articles (STUB)
        In production: Use NLP to extract numbers, analyst expectations, sentiment
        """
        # STUB: Simple sentiment heuristic
        positive_keywords = ['beat', 'exceed', 'strong', 'growth', 'up']
        negative_keywords = ['miss', 'weak', 'decline', 'down', 'below']
        
        positive_count = 0
        negative_count = 0
        
        for article in articles[:5]:  # Top 5 articles
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            positive_count += sum(1 for kw in positive_keywords if kw in text)
            negative_count += sum(1 for kw in negative_keywords if kw in text)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        # Simple ratio (replace with proper NLP)
        sentiment = positive_count / (positive_count + negative_count)
        
        # Map sentiment to probability based on query direction
        # TODO: Parse market question to determine if "yes" = positive or negative
        return sentiment
    
    async def _calculate_sports_fair_value(self, query: str, market: dict) -> float:
        """
        Sports: Historical stats, current standings, betting markets
        Strategy: Scrape sports stats sites, compare to betting odds
        """
        # STUB: Would integrate ESPN API, sports reference, or betting markets
        logger.debug(f"[STUB] Sports fair value for: {query}")
        return self._extract_market_probability(market)
    
    async def detect_arbitrage(self, markets: List[dict]) -> List[Tuple[dict, dict, str]]:
        """
        Detect cross-market arbitrage opportunities
        E.g., "Trump wins primary" prob > "Trump wins general" prob (logical inconsistency)
        """
        arb_opportunities = []
        
        for i, m1 in enumerate(markets):
            for m2 in markets[i+1:]:
                # Check for related markets
                if self._are_markets_related(m1, m2):
                    prob1 = self._extract_market_probability(m1)
                    prob2 = self._extract_market_probability(m2)
                    
                    # Check for logical inconsistency
                    if self._is_arbitrage(m1, m2, prob1, prob2):
                        reason = f"Arb: {m1['title'][:30]}... ({prob1:.2f}) vs {m2['title'][:30]}... ({prob2:.2f})"
                        arb_opportunities.append((m1, m2, reason))
                        logger.info(f"🎯 Arbitrage detected: {reason}")
        
        return arb_opportunities
    
    def _are_markets_related(self, m1: dict, m2: dict) -> bool:
        """Check if two markets are logically related"""
        # Simple heuristic: Shared keywords
        words1 = set(m1['title'].lower().split())
        words2 = set(m2['title'].lower().split())
        shared = words1 & words2
        return len(shared) >= 2  # At least 2 common words
    
    def _is_arbitrage(self, m1: dict, m2: dict, prob1: float, prob2: float) -> bool:
        """
        Detect arbitrage based on logical constraints
        Example: If m1 implies m2, then P(m1) <= P(m2)
        """
        # STUB: Simple price discrepancy (enhance with logical inference)
        return abs(prob1 - prob2) > Config.DEVIATION_THRESHOLD and prob1 > prob2 + 0.1
