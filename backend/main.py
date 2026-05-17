"""Composition root for the Sommelier API.

Keep this file thin: env bootstrap, logging, app construction, middleware,
and router includes only. Endpoint handlers live in `backend/routes/`.
"""
# bootstrap must import first — it runs load_dotenv before any module that
# reads env vars at import time (e.g. recommender, profile).
import bootstrap  # noqa: F401

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cache import init_db, purge_expired
from wine_reviews import seed_wine_reviews
from logging_setup import configure_logging
from middleware import install as install_middleware
from routes.debug import router as debug_router
from routes.history import router as history_router
from routes.inventory import router as inventory_router
from routes.profile import router as profile_router
from routes.recommend import router as recommend_router

configure_logging()
logger = logging.getLogger("sommelier.api")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
install_middleware(app)

init_db()
logger.info("cache_purge_on_startup expired_entries=%d", purge_expired())
seed_wine_reviews()

app.include_router(debug_router)
app.include_router(history_router)
app.include_router(inventory_router)
app.include_router(profile_router)
app.include_router(recommend_router)
