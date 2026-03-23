from src.routers.user import auth_router
from src.routers.document import document_router
from src.routers.assistant import assistant_router

__all__ = [
    "auth_router",
    "document_router",
    "assistant_router",
]
