"""
Ozon marketplace integration service.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import MarketplaceClient, logger

class OzonClient(MarketplaceClient):
    """Client for Ozon API."""
    
    def __init__(self, api_key: str, client_id: str):
        """
        Initialize Ozon client.
        
        Args:
            api_key: Ozon API key
            client_id: Ozon client ID
        """
        super().__init__(api_key, marketplace='ozon')
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
            logger.info(f"Validating Ozon API key with Client ID: {self.client_id}")
            logger.info("Headers for validation request:")
            headers = self._get_headers()
            for key, value in headers.items():
                if key.lower() in ['api-key', 'client-id']:
                    logger.info(f"{key}: {'*' * len(value)}")
                else:
                    logger.info(f"{key}: {value}")
            
            # Use seller info endpoint for validation
            logger.info("Making validation request to Ozon API")
            await self._make_request(
                method="POST",
                url=f"{self.base_url}/v3/product/info/stocks",
                headers=headers,
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
            logger.info("API key validation successful")
            return True
        except ValueError as e:
            logger.error(f"API key validation failed with ValueError: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"API key validation failed with error: {str(e)}")
            return False

    async def _get_action_products(self, action_id: int) -> List[Dict]:
        """
        Get products participating in a specific action.
        
        Args:
            action_id: Action ID
            
        Returns:
            List[Dict]: List of products in the action
        """
        response = await self._make_request(
            method="POST",
            url=f"{self.base_url}/v1/actions/products",
            headers=self._get_headers(),
            json={"action_id": action_id}
        )
        
        return response.get("result", {}).get("products", [])

    async def _get_hotsale_products(self) -> List[Dict]:
        """
        Get products participating in Hot Sale promotions.
        
        Returns:
            List[Dict]: List of products in Hot Sale promotions
        """
        # Get list of available Hot Sales
        response = await self._make_request(
            method="POST",
            url=f"{self.base_url}/v1/actions/hotsales/list",
            headers=self._get_headers(),
            json={}
        )
        
        # Get products for each Hot Sale
        products = []
        hot_sales = response.get("result", {}).get("actions", [])
        logger.info(f"Found {len(hot_sales)} Hot Sales")
        
        for hot_sale in hot_sales:
            hot_sale_products = await self._make_request(
                method="POST",
                url=f"{self.base_url}/v1/actions/hotsales/products",
                headers=self._get_headers(),
                json={"action_id": hot_sale["id"]}
            )
            products.extend(hot_sale_products.get("result", {}).get("products", []))
        
        return products
    
    async def get_promo_products(self) -> List[Dict]:
        """
        Get summary of all products participating in promotions.
        
        Returns:
            List[Dict]: List of promotions with product counts
            
        Raises:
            ValueError: If API key is invalid
            ConnectionError: If connection failed
        """
        all_promotions = []
        
        try:
            # 1. Получаем список всех акций
            logger.info("Getting list of all Ozon actions")
            actions_response = await self._make_request(
                method="GET",
                url=f"{self.base_url}/v1/actions",
                headers=self._get_headers()
            )
            
            actions = actions_response.get("result", [])
            logger.info(f"Found {len(actions)} actions")
            
            # 2. Для каждой акции получаем список товаров
            for action in actions:
                action_id = action["id"]
                action_title = action["title"]
                action_type = action["action_type"]
                
                logger.info(f"Getting products for action {action_title} (ID: {action_id}, Type: {action_type})")
                
                products = await self._get_action_products(action_id)
                
                if products:
                    all_promotions.append({
                        "id": action_id,
                        "title": action_title,
                        "type": action_type,
                        "start_date": action["date_start"],
                        "end_date": action["date_end"],
                        "products": products,
                        "products_count": len(products)
                    })
            
            # 3. Получаем товары из Hot Sale акций
            logger.info("Getting Hot Sale products")
            hot_sale_products = await self._get_hotsale_products()
            
            if hot_sale_products:
                all_promotions.append({
                    "id": "hot_sale",
                    "title": "Hot Sale",
                    "type": "hot_sale",
                    "products": hot_sale_products,
                    "products_count": len(hot_sale_products)
                })
            
            logger.info(f"Total promotions found: {len(all_promotions)}")
            for promo in all_promotions:
                logger.info(
                    f"Promotion: {promo['title']} ({promo['type']})\n"
                    f"Products: {promo['products_count']}"
                )
            
            return all_promotions
            
        except Exception as e:
            logger.error(f"Error getting promo products: {str(e)}")
            raise
