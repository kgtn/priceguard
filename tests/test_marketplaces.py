"""
Tests for marketplace clients.
"""

import pytest
from unittest.mock import AsyncMock, patch

from services.marketplaces.factory import MarketplaceFactory

@pytest.mark.asyncio
async def test_marketplace_factory_creation(settings):
    """Test marketplace factory creation."""
    factory = MarketplaceFactory(settings.encryption_key)
    assert factory is not None

@pytest.mark.asyncio
async def test_api_key_encryption(settings):
    """Test API key encryption/decryption."""
    factory = MarketplaceFactory(settings.encryption_key)
    api_key = "test_key_123"
    
    encrypted = factory.encrypt_api_key(api_key)
    decrypted = factory.decrypt_api_key(encrypted)
    
    assert decrypted == api_key
    assert encrypted != api_key

@pytest.mark.asyncio
async def test_ozon_client_creation(marketplace_factory: MarketplaceFactory):
    """Test Ozon client creation."""
    with patch("services.marketplaces.ozon.OzonClient.validate_api_key") as mock:
        mock.return_value = True
        
        encrypted_key = marketplace_factory.encrypt_api_key("test_key")
        client = await marketplace_factory.create_client(
            marketplace="ozon",
            encrypted_key=encrypted_key,
            client_id="test_client"
        )
        assert client is not None

@pytest.mark.asyncio
async def test_wb_client_creation(marketplace_factory: MarketplaceFactory):
    """Test Wildberries client creation."""
    with patch("services.marketplaces.wildberries.WildberriesClient.validate_api_key") as mock:
        mock.return_value = True
        
        encrypted_key = marketplace_factory.encrypt_api_key("test_key")
        client = await marketplace_factory.create_client(
            marketplace="wildberries",
            encrypted_key=encrypted_key
        )
        assert client is not None

@pytest.mark.asyncio
async def test_invalid_marketplace(marketplace_factory: MarketplaceFactory):
    """Test invalid marketplace handling."""
    with pytest.raises(ValueError, match="Unsupported marketplace"):
        encrypted_key = marketplace_factory.encrypt_api_key("test_key")
        await marketplace_factory.create_client(
            marketplace="invalid",
            encrypted_key=encrypted_key
        )

@pytest.mark.asyncio
async def test_invalid_api_key(marketplace_factory: MarketplaceFactory):
    """Test invalid API key handling."""
    with patch("services.marketplaces.ozon.OzonClient.validate_api_key") as mock:
        mock.return_value = False
        
        with pytest.raises(ValueError, match="Invalid ozon API key"):
            encrypted_key = marketplace_factory.encrypt_api_key("invalid_key")
            await marketplace_factory.create_client(
                marketplace="ozon",
                encrypted_key=encrypted_key,
                client_id="test_client"
            )
