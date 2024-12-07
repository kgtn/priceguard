"""
Tests for marketplace clients.
"""

import pytest
from unittest.mock import AsyncMock, patch

from services.marketplaces.factory import MarketplaceClientFactory

@pytest.mark.asyncio
async def test_ozon_client_creation(client_factory: MarketplaceClientFactory):
    """Test Ozon client creation."""
    client = await client_factory.get_ozon_client("test_key")
    assert client is not None

@pytest.mark.asyncio
async def test_wb_client_creation(client_factory: MarketplaceClientFactory):
    """Test Wildberries client creation."""
    client = await client_factory.get_wildberries_client("test_key")
    assert client is not None

@pytest.mark.asyncio
async def test_ozon_hot_sales():
    """Test Ozon hot sales API."""
    with patch("services.marketplaces.ozon.OzonClient.get_hot_sales") as mock:
        mock.return_value = AsyncMock(return_value=[
            {
                "id": "123",
                "name": "Test Product",
                "price": 1000,
                "action_price": 800,
                "stock": 10
            }
        ])
        
        client = await MarketplaceClientFactory().get_ozon_client("test_key")
        result = await client.get_hot_sales()
        
        assert len(result) == 1
        assert result[0]["id"] == "123"
        assert result[0]["price"] == 1000

@pytest.mark.asyncio
async def test_wb_auto_promotions():
    """Test Wildberries auto promotions API."""
    with patch("services.marketplaces.wildberries.WildberriesClient.get_auto_promotions") as mock:
        mock.return_value = AsyncMock(return_value=[
            {
                "id": "456",
                "name": "Test Promotion",
                "discount": 20,
                "products_count": 5
            }
        ])
        
        client = await MarketplaceClientFactory().get_wildberries_client("test_key")
        result = await client.get_auto_promotions()
        
        assert len(result) == 1
        assert result[0]["id"] == "456"
        assert result[0]["discount"] == 20
