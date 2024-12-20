"""
Base marketplace client for the PriceGuard bot.
File: src/services/marketplaces/base.py
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import aiohttp
from core.logging import get_logger
from .queue import QueueManager

logger = get_logger(__name__)

class MarketplaceClient(ABC):
    """Base class for marketplace clients."""
    
    def __init__(self, api_key: str, marketplace: str):
        """
        Initialize marketplace client.
        
        Args:
            api_key: API key for marketplace
            marketplace: Marketplace name for queue selection
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.queue = QueueManager.get_queue(marketplace)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate the API key."""
        pass
    
    @abstractmethod
    async def get_promo_products(self) -> List[Dict]:
        """Get list of products in promotions."""
        pass
    
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request to marketplace API.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            json: JSON body
            params: Query parameters
            
        Returns:
            Dict: Response data
            
        Raises:
            ValueError: If API key is invalid
            ConnectionError: If connection failed
            Exception: For other errors
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        async def _do_request():
            logger.info(f"Making {method} request to:\n{url}")
            
            # Log headers
            headers_str = "\n".join(
                f"    {key}: {'*' * 8 if key.lower() in ['api-key', 'client-id', 'authorization'] else value}"
                for key, value in (headers or {}).items()
            )
            if headers_str:
                logger.info(f"Request headers:\n{headers_str}")
            
            # Log request body/params
            if json:
                logger.info(f"Request body:\n{json}")
            if params:
                logger.info(f"Request params:\n{params}")
            
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                params=params
            ) as response:
                # Log response info
                content_type = response.headers.get('content-type', '')
                logger.info(f"Response status: {response.status}\nContent-Type: {content_type}")
                
                if not content_type.startswith('application/json'):
                    text = await response.text()
                    logger.error(f"Unexpected response type: {content_type}\nBody: {text}")
                    raise ValueError("Invalid API key or Client ID")
                
                response_data = await response.json()
                logger.info("Response data received")
                
                if response.status == 401:
                    logger.error("Authentication failed: Invalid API key")
                    raise ValueError("Invalid API key")
                elif response.status == 403:
                    logger.error("Authorization failed: Invalid Client ID")
                    raise ValueError("Invalid Client ID")
                elif response.status == 404:
                    logger.error("Not found: Invalid API endpoint or Client ID")
                    raise ValueError("Invalid API endpoint or Client ID")
                elif response.status >= 500:
                    logger.error(f"Server error: {response.status}")
                    raise ConnectionError(f"Marketplace API error: {response.status}")
                elif response.status >= 400:
                    error_data = await response.json()
                    logger.error(f"API error response:\n{error_data}")
                    raise ValueError(error_data.get("message", "Unknown error"))
                elif response.status >= 200 and response.status < 300:
                    return response_data
                else:
                    logger.error(f"Unknown response status: {response.status}")
                    raise Exception(f"Unknown response status: {response.status}")
                    
                return response_data
        
        return await self.queue.execute(_do_request)
