from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import api_router
from app.core.config import settings


FRONTEND_INDEX = Path(__file__).parent / "frontend" / "index.html"


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(dict.fromkeys([*settings.cors_origins, "null"])),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    frontend_path = Path(__file__).parent / "frontend"
    desktop_renderer_path = Path(__file__).parent / "desktop" / "renderer"
    
    from fastapi.staticfiles import StaticFiles
    import os
    if os.path.exists(frontend_path):
        app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")
    if os.path.exists(desktop_renderer_path):
        app.mount("/offline-pos", StaticFiles(directory=desktop_renderer_path, html=True), name="offline-pos")

    @app.get("/", include_in_schema=False)
    def serve_frontend() -> FileResponse:
        return FileResponse(FRONTEND_INDEX)

    return app


app = create_app()
