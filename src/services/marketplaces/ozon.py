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
        Get summary of products participating in Hot Sale promotions.
        
        Returns:
            List[Dict]: List of promotions with product counts
            
        Raises:
            ValueError: If API key is invalid
            ConnectionError: If connection failed
        """
        try:
            # First, get list of available Hot Sales
            response = await self._make_request(
                method="POST",
                url=f"{self.base_url}/v1/actions/hotsales/list",
                headers=self._get_headers(),
                json={}
            )
            
            hotsales = response.get("result", [])
            if not hotsales:
                return []
                
            promotions = []
            for hotsale in hotsales:
                # Проверяем только акции, в которых участвует продавец
                if not hotsale.get("is_participating"):
                    continue
                    
                # Get products for this Hot Sale
                products_response = await self._make_request(
                    method="POST",
                    url=f"{self.base_url}/v1/actions/hotsales/products",
                    headers=self._get_headers(),
                    json={
                        "hotsale_id": hotsale["hotsale_id"]
                    }
                )
                
                # Get products list from response
                products = products_response.get("result", {}).get("products", [])
                active_products = len([p for p in products if p.get("is_active")])
                
                promotions.append({
                    "id": str(hotsale["hotsale_id"]),
                    "name": hotsale.get("title", "Hot Sale"),
                    "products_count": active_products,
                    "date_start": hotsale.get("date_start"),
                    "date_end": hotsale.get("date_end")
                })
            
            return promotions
            
        except Exception as e:
            logger.error(f"Error getting Ozon Hot Sale products: {e}")
            raise
