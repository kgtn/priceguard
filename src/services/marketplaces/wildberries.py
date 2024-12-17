"""
Wildberries marketplace integration service.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
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
        self.base_url = "https://suppliers-api.wildberries.ru"
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
            # Get current time in UTC
            now = datetime.utcnow()
            # Set start time to 1 month ago
            start_time = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            # Set end time to 1 year in future
            end_time = (now + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Get promotion details
            response = await self._make_request(
                method="GET",
                url=f"{self.calendar_url}/api/v1/calendar/promotions",
                headers=self._get_headers(),
                params={
                    "startDateTime": start_time,
                    "endDateTime": end_time,
                    "allPromo": "true",
                    "limit": 1000,
                    "offset": 0
                }
            )
            
            auto_promotions = []
            for promo in response.get("data", {}).get("promotions", []):
                if promo.get("type") == "auto":
                    # Получаем детальную информацию о товарах в акции
                    promo_details = await self._get_promo_details(promo["id"])
                    
                    auto_promotions.append({
                        "id": promo["id"],
                        "name": promo.get("name", ""),
                        "products_count": promo_details.get("products_count", 0),
                        "date_start": promo.get("startDateTime"),
                        "date_end": promo.get("endDateTime")
                    })
                    
            return auto_promotions
            
        except Exception as e:
            logger.error(f"Error getting promotions: {str(e)}")
            raise

    async def _get_promo_details(self, promo_id: str) -> Dict:
        """
        Get detailed information about products in promotion.
        
        Args:
            promo_id: Promotion ID
            
        Returns:
            Dict with promotion details including products count
        """
        try:
            response = await self._make_request(
                method="GET",
                url=f"{self.calendar_url}/api/v1/calendar/promotions/details",
                headers=self._get_headers(),
                params={
                    "id": promo_id
                }
            )
            
            products_count = len(response.get("data", {}).get("products", []))
            return {
                "products_count": products_count
            }
            
        except Exception as e:
            logger.error(f"Error getting promotion details: {str(e)}")
            return {"products_count": 0}
