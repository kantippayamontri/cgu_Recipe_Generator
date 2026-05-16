"""Pydantic schemas for search API."""

from pydantic import BaseModel, Field

from server.schemas.recipe import RecipeResponse


class CategoryInfo(BaseModel):
    """Category with recipe count for popularity display."""

    name: str
    count: int


class SearchRequest(BaseModel):
    """Search request payload from the frontend."""

    query: str = ""
    filters: list[str] = Field(default_factory=list)
    limit: int | None = Field(default=None, le=20)


class SearchResponse(BaseModel):
    """Search results returned to the frontend."""

    query: str
    total: int
    recipes: list[RecipeResponse]
