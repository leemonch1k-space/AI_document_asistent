from fastapi import FastAPI
import logging

from src.routers import document_router, auth_router, assistant_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(assistant_router)

log = logging.getLogger(__name__)
log.info("Server running...")
