"""Pydantic schemas for recipe API responses."""

from pydantic import BaseModel


class IngredientResponse(BaseModel):
    """Ingredient within a recipe."""

    name: str
    amount: str


class InstructionResponse(BaseModel):
    """Single cooking instruction."""

    step: int
    description: str


class RecipeResponse(BaseModel):
    """Complete recipe returned to the frontend."""

    id: int
    title: str
    description: str
    image: str
    categories: list[str]
    cookTimeMinutes: int
    servings: int
    ingredients: list[IngredientResponse]
    instructions: list[InstructionResponse]
