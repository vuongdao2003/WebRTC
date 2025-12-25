from .ws_detection import router
from .token import router as token_router
from .auth import router as auth_router

__all__ = ["router", "token_router", "auth_router"]
