"""
Ozon marketplace integration service.
File: src/services/marketplaces/ozon.py
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import MarketplaceClient, logger

class OzonClient(MarketplaceClient):
    def __init__(self, api_key: str, client_id: str):
        super().__init__(api_key)
        self.client_id = client_id
        self.base_url = "https://api-seller.ozon.ru"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Ozon API requests."""
        return {
            "Client-Id": self.client_id,
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
    async def validate_api_key(self) -> bool:
        """
        Validate Ozon API key by making a test request.
        
        Returns:
            bool: True if API key is valid
            
        Raises:
            ValueError: If API key is invalid
        """
        try:
            # Use seller info endpoint for validation
            await self._make_request(
                method="POST",
                url=f"{self.base_url}/v3/product/info/stocks",
                headers=self._get_headers(),
                json={
                    "filter": {
                            "offer_id": [
                                "136834"
                            ],
                            "product_id": [
                                "214887921"
                            ],
                            "visibility": "ALL"
                        },
                        "last_id": "",
                        "limit": 100
                }
            )
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
            
    async def get_promo_products(self) -> List[Dict]:
        """
        Get list of products participating in Hot Sale promotions.
        
        Returns:
            List[Dict]: List of products with their promotion details
            
        Raises:
            ValueError: If API key is invalid
            ConnectionError: If connection failed
        """
        products = []
        
        try:
            # Get Hot Sale products
            response = await self._make_request(
                method="POST",
                url=f"{self.base_url}/v1/actions/hotsales/products",
                headers=self._get_headers(),
                json={}
            )
            
            for product in response.get("result", {}).get("products", []):
                if product.get("is_active"):
                    products.append({
                        "id": product["id"],
                        "action_price": product.get("action_price", 0),
                        "max_action_price": product.get("max_action_price", 0),
                        "date_promo": product.get("date_day_promo", ""),
                        "stock": product.get("stock", 0),
                        "min_stock": product.get("min_stock", 0),
                        "is_active": product.get("is_active", False)
                    })
                    
            return products
            
        except Exception as e:
            logger.error(f"Error getting Ozon Hot Sale products: {e}")
            raise
