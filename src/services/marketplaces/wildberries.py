"""
Wildberries marketplace integration service.
File: src/services/marketplaces/wildberries.py
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import MarketplaceClient, logger

class WildberriesClient(MarketplaceClient):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://suppliers-api.wildberries.ru"
        self.calendar_url = "https://dp-calendar-api.wildberries.ru"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Wildberries API requests."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
    async def validate_api_key(self) -> bool:
        """
        Validate Wildberries API key by making a test request.
        
        Returns:
            bool: True if API key is valid
            
        Raises:
            ValueError: If API key is invalid
        """
        try:
            await self._make_request(
                method="GET",
                url=f"{self.base_url}/public/api/v1/info",
                headers=self._get_headers()
            )
            return True
        except ValueError:
            raise
        except Exception:
            return False
            
    async def get_promo_products(self) -> List[Dict]:
        """
        Get list of products participating in auto promotions.
        
        Returns:
            List[Dict]: List of promotions with their details
            
        Raises:
            ValueError: If API key is invalid
            ConnectionError: If connection failed
        """
        promotions = []
        
        try:
            # Get promotion details
            response = await self._make_request(
                method="GET",
                url=f"{self.calendar_url}/api/v1/calendar/promotions/details",
                headers=self._get_headers()
            )
            
            for promo in response.get("data", {}).get("promotions", []):
                # Only include auto promotions
                if promo.get("type") == "auto":
                    promotions.append({
                        "id": promo["id"],
                        "name": promo.get("name", ""),
                        "description": promo.get("description", ""),
                        "advantages": promo.get("advantages", []),
                        "start_date": promo.get("startDateTime", ""),
                        "end_date": promo.get("endDateTime", ""),
                        "products_in_promo": promo.get("inPromoActionTotal", 0),
                        "products_with_stock": promo.get("inPromoActionLeftovers", 0),
                        "participation_percentage": promo.get("participationPercentage", 0),
                        "excluded_products": promo.get("exceptionProductsCount", 0)
                    })
                    
            return promotions
            
        except Exception as e:
            logger.error(f"Error getting Wildberries auto promotions: {e}")
            raise
