"""
Wildberries marketplace integration service.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import MarketplaceClient, logger

class WildberriesClient(MarketplaceClient):
    """Client for Wildberries API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Wildberries client.
        
        Args:
            api_key: Wildberries API key
        """
        super().__init__(api_key, marketplace='wildberries')
        self.base_url = "https://discounts-prices-api-sandbox.wildberries.ru"
        self.calendar_url = "https://dp-calendar-api.wildberries.ru"
        self.common_url = "https://common-api.wildberries.ru"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Wildberries API requests."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def validate_api_key(self) -> bool:
        """
        Validate Wildberries API key by making a test request to /ping endpoint.
        
        Returns:
            bool: True if API key is valid
            
        Raises:
            ValueError: If API key is invalid
        """
        try:
            # Use ping endpoint for validation
            await self._make_request(
                method="GET",
                url=f"{self.common_url}/ping",
                headers=self._get_headers()
            )
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    
    async def get_promo_products(self) -> List[Dict]:
        """
        Get summary of products participating in auto promotions.
        
        Returns:
            List[Dict]: List of auto promotions with product counts
            
        Raises:
            ValueError: If API key is invalid
            ConnectionError: If connection failed
        """
        try:
            # Get promotion details
            response = await self._make_request(
                method="GET",
                url=f"{self.calendar_url}/api/v1/calendar/promotions/details",
                headers=self._get_headers()
            )
            
            auto_promotions = []
            for promo in response.get("data", {}).get("promotions", []):
                if promo.get("type") == "auto":
                    auto_promotions.append({
                        "id": promo["id"],
                        "name": promo.get("name", ""),
                        "products_count": promo.get("inPromoActionTotal", 0),
                        "date_start": promo.get("dateStart"),
                        "date_end": promo.get("dateEnd")
                    })
                    
            return auto_promotions
            
        except Exception as e:
            logger.error(f"Error getting Wildberries auto promotions: {e}")
            raise
