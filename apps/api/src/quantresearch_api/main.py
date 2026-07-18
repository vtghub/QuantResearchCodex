from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantresearch_api.api import api_router
from quantresearch_api.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="QuantResearchCodex API",
        version="0.1.0",
        description="Tenant-aware quant research, backtesting, and trading platform API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
