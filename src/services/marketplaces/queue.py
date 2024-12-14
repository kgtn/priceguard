"""
Queue management system for marketplace API requests.
"""

import asyncio
import time
from typing import Dict, Optional, Any, Callable, Awaitable
from datetime import datetime, timedelta
from collections import deque
from core.logging import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int, min_interval: float):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests per minute
            min_interval: Minimum interval between requests in seconds
        """
        self.requests_per_minute = requests_per_minute
        self.min_interval = min_interval
        self.request_times = deque(maxlen=requests_per_minute)
        self.last_request_time = 0
        
    async def acquire(self):
        """Wait until request can be made according to rate limits."""
        now = time.time()
        
        # Check minimum interval between requests
        if self.last_request_time > 0:
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
                now = time.time()
        
        # Check requests per minute limit
        if len(self.request_times) == self.requests_per_minute:
            oldest = self.request_times[0]
            if now - oldest < 60:
                wait_time = 60 - (now - oldest)
                await asyncio.sleep(wait_time)
                now = time.time()
        
        self.request_times.append(now)
        self.last_request_time = now

class MarketplaceQueue:
    """Base class for marketplace request queues."""
    
    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize marketplace queue.
        
        Args:
            rate_limiter: Rate limiter instance
        """
        self.rate_limiter = rate_limiter
        self.retry_delays = [1, 2, 5, 10, 30]  # Delays between retries in seconds
        
    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute API request with rate limiting and retries.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Any: Function result
            
        Raises:
            Exception: If all retries failed
        """
        await self.rate_limiter.acquire()
        
        for attempt, delay in enumerate(self.retry_delays):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, ValueError) and "Invalid API key" in str(e):
                    logger.error(f"Invalid API credentials: {str(e)}")
                    raise
                
                if attempt == len(self.retry_delays) - 1:
                    logger.error(f"All retry attempts failed for {func.__name__}: {str(e)}")
                    raise
                
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{len(self.retry_delays)}): {str(e)}. "
                    f"Retrying in {delay} seconds..."
                )
                await asyncio.sleep(delay)

class OzonQueue(MarketplaceQueue):
    """Queue for Ozon API requests."""
    
    def __init__(self):
        """Initialize Ozon queue with specific rate limits."""
        super().__init__(RateLimiter(requests_per_minute=30, min_interval=2))

class WildberriesQueue(MarketplaceQueue):
    """Queue for Wildberries API requests."""
    
    def __init__(self):
        """Initialize Wildberries queue with specific rate limits."""
        super().__init__(RateLimiter(requests_per_minute=30, min_interval=2))

class QueueManager:
    """Manager for marketplace queues."""
    
    _instance = None
    _queues: Dict[str, MarketplaceQueue] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_queue(cls, marketplace: str) -> MarketplaceQueue:
        """
        Get queue for specified marketplace.
        
        Args:
            marketplace: Marketplace name ('ozon' or 'wildberries')
            
        Returns:
            MarketplaceQueue: Queue instance
            
        Raises:
            ValueError: If marketplace is not supported
        """
        if marketplace not in cls._queues:
            if marketplace.lower() == 'ozon':
                cls._queues[marketplace] = OzonQueue()
            elif marketplace.lower() == 'wildberries':
                cls._queues[marketplace] = WildberriesQueue()
            else:
                raise ValueError(f"Unsupported marketplace: {marketplace}")
        
        return cls._queues[marketplace]
