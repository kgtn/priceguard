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
        try:
            encrypted = self.fernet.encrypt(api_key.encode()).decode()
            logger.debug(f"API key encrypted successfully")
            return encrypted
        except Exception as e:
            logger.error(f"Error encrypting API key: {str(e)}")
            raise
        
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt stored API key.
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            str: Decrypted API key
        """
        try:
            decrypted = self.fernet.decrypt(encrypted_key.encode()).decode()
            logger.debug(f"API key decrypted successfully")
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting API key: {str(e)}")
            raise
        
    async def create_client(
        self,
        marketplace: str,
        api_key: str,
        client_id: Optional[str] = None,
        is_encrypted: bool = False
    ) -> Union[OzonClient, WildberriesClient]:
        """
        Create and validate marketplace client.
        
        Args:
            marketplace: Marketplace name ('ozon' or 'wildberries')
            api_key: API key (encrypted or not)
            client_id: Ozon client ID (required for Ozon)
            is_encrypted: Whether the API key is encrypted
            
        Returns:
            Union[OzonClient, WildberriesClient]: Marketplace client instance
            
        Raises:
            ValueError: If API key is invalid or required parameters are missing
        """
        try:
            if is_encrypted:
                api_key = self.decrypt_api_key(api_key)
            
            if marketplace.lower() == 'ozon':
                if not client_id:
                    raise ValueError("client_id is required for Ozon API")
                client = OzonClient(api_key=api_key, client_id=client_id)
            elif marketplace.lower() == 'wildberries':
                client = WildberriesClient(api_key=api_key)
            else:
                raise ValueError(f"Unsupported marketplace: {marketplace}")
                
            return client
            
        except Exception as e:
            logger.error(f"Error creating {marketplace} client: {str(e)}")
            raise

    async def get_ozon_client(self, encrypted_key: str, client_id: str) -> OzonClient:
        """
        Get Ozon client instance.
        
        Args:
            encrypted_key: Encrypted API key
            client_id: Ozon client ID
            
        Returns:
            OzonClient: Ozon client instance
        """
        return await self.create_client('ozon', encrypted_key, client_id=client_id, is_encrypted=True)

    async def get_wildberries_client(self, encrypted_key: str) -> WildberriesClient:
        """
        Get Wildberries client instance.
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            WildberriesClient: Wildberries client instance
        """
        return await self.create_client('wildberries', encrypted_key, is_encrypted=True)
