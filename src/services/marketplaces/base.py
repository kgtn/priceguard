"""
Base marketplace client for the PriceGuard bot.
File: src/services/marketplaces/base.py
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import aiohttp
from core.logging import get_logger

logger = get_logger(__name__)

class MarketplaceClient(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
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
            
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                params=params
            ) as response:
                response_data = await response.json()
                
                if response.status == 401:
                    raise ValueError("Invalid API key")
                elif response.status >= 500:
                    raise ConnectionError(f"Marketplace API error: {response.status}")
                elif response.status >= 400:
                    raise Exception(f"Request error: {response_data.get('message', 'Unknown error')}")
                    
                return response_data
                
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(f"Failed to connect to marketplace API: {str(e)}")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
