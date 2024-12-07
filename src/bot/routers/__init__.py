"""
Bot routers package.
"""

from .admin import router as admin_router
from .user import router as user_router
from .payment import router as payment_router

__all__ = ['admin_router', 'user_router', 'payment_router']
