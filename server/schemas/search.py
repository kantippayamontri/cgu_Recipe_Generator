"""Pydantic schemas for search API."""

from pydantic import BaseModel, Field

from server.schemas.recipe import RecipeResponse


class SearchRequest(BaseModel):
    """Search request payload from the frontend."""

    query: str = ""
    filters: list[str] = Field(default_factory=list)
    limit: int | None = None


class SearchResponse(BaseModel):
    """Search results returned to the frontend."""

    query: str
    total: int
    recipes: list[RecipeResponse]
