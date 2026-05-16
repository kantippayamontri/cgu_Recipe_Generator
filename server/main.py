"""FastAPI application entry point."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import recipes, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

app = FastAPI(
    title="Recipe Search Engine",
    description="NLP-powered recipe search using TF-IDF and N-grams",
    version="0.1.0",
)

# CORS: allow all origins (backend is behind nginx proxy manager)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under /api/v1
app.include_router(search.router, prefix="/api/v1/search")
app.include_router(recipes.router, prefix="/api/v1/recipes")


@app.get("/api/v1/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
