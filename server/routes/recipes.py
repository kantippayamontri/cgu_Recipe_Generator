"""Recipe CRUD endpoints."""

from fastapi import APIRouter, HTTPException

from server.schemas.recipe import RecipeResponse
from server.services import search_service

router = APIRouter()


@router.get(
    "/{recipe_id}",
    response_model=RecipeResponse,
    status_code=200,
    summary="Get a single recipe by ID",
)
async def get_recipe(recipe_id: int) -> RecipeResponse:
    """Fetch recipe details."""
    recipe = await search_service.get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get(
    "/{recipe_id}/similar",
    response_model=list[RecipeResponse],
    status_code=200,
    summary="Find similar recipes",
)
async def get_similar(recipe_id: int) -> list[RecipeResponse]:
    """Return recipes similar to the given recipe using TF-IDF."""
    return await search_service.get_similar_recipes(recipe_id)
