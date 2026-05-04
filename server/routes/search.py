"""Search endpoints."""

from fastapi import APIRouter, Query

from server.schemas.search import CategoryInfo, SearchRequest, SearchResponse
from server.services import search_service

router = APIRouter()


@router.post(
    "",
    response_model=SearchResponse,
    status_code=200,
    summary="Search recipes by ingredients or text",
)
async def search(request: SearchRequest) -> SearchResponse:
    """Search recipes using TF-IDF similarity."""
    return await search_service.search_recipes(request)


@router.get(
    "/suggest",
    response_model=list[str],
    status_code=200,
    summary="Get autocomplete suggestions for search query",
)
async def suggestions(query: str = Query(default="")) -> list[str]:
    """Return autocomplete suggestions."""
    return await search_service.get_suggestions(query)


@router.get(
    "/categories",
    response_model=list[CategoryInfo],
    status_code=200,
    summary="Get all recipe categories with counts for filters",
)
async def categories() -> list[CategoryInfo]:
    """Return unique recipe categories sorted by popularity (recipe count desc)."""
    result = await search_service.get_categories()
    return [CategoryInfo(name=name, count=count) for name, count in result]
