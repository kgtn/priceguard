"""
Marketplace client factory for the PriceGuard bot.
File: src/services/marketplaces/factory.py
"""

from typing import Dict, Optional, Union
from cryptography.fernet import Fernet
from .ozon import OzonClient
from .wildberries import WildberriesClient
from core.logging import get_logger

logger = get_logger(__name__)

class MarketplaceFactory:
    def __init__(self, encryption_key: str):
        """
        Initialize marketplace factory.
        
        Args:
            encryption_key: Key for encrypting/decrypting API keys
        """
        self.fernet = Fernet(encryption_key.encode())
        
    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key for storage.
        
        Args:
            api_key: API key to encrypt
            
        Returns:
            str: Encrypted API key
        """
        return self.fernet.encrypt(api_key.encode()).decode()
        
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt stored API key.
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            str: Decrypted API key
        """
        return self.fernet.decrypt(encrypted_key.encode()).decode()
        
    async def create_client(
        self,
        marketplace: str,
        encrypted_key: str,
        client_id: Optional[str] = None
    ) -> Union[OzonClient, WildberriesClient]:
        """
        Create and validate marketplace client.
        
        Args:
            marketplace: Marketplace name ('ozon' or 'wildberries')
            encrypted_key: Encrypted API key
            client_id: Ozon client ID (required for Ozon)
            
        Returns:
            Union[OzonClient, WildberriesClient]: Marketplace client instance
            
        Raises:
            ValueError: If API key is invalid or required parameters are missing
        """
        try:
            api_key = self.decrypt_api_key(encrypted_key)
            
            if marketplace.lower() == 'ozon':
                if not client_id:
                    raise ValueError("client_id is required for Ozon API")
                client = OzonClient(api_key=api_key, client_id=client_id)
            elif marketplace.lower() == 'wildberries':
                client = WildberriesClient(api_key=api_key)
            else:
                raise ValueError(f"Unsupported marketplace: {marketplace}")
                
            # Validate API key
            async with client:
                is_valid = await client.validate_api_key()
                if not is_valid:
                    raise ValueError(f"Invalid {marketplace} API key")
                    
            return client
            
        except Exception as e:
            logger.error(f"Error creating {marketplace} client: {str(e)}")
            raise
