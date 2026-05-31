import axios from 'axios'
import type { CategoryInfo, Recipe, SearchRequest, SearchResponse, SearchSuggestion } from '../types/recipe.ts'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
})

function mapBackendRecipe(r: {
  id: number
  title: string
  description: string
  image: string
  categories: string[]
  cookTimeMinutes: number
  servings: number
  ingredients: { name: string; amount: string }[]
  instructions: { step: number; description: string }[]
}): Recipe {
  return {
    id: r.id,
    title: r.title,
    description: r.description || r.title,
    image: r.image || 'https://img.magnific.com/premium-vector/file-folder-mascot-character-design-vector_166742-4413.jpg?semt=ais_hybrid&w=740&q=80',
    categories: r.categories,
    cookTimeMinutes: r.cookTimeMinutes,
    servings: r.servings,
    ingredients: r.ingredients,
    instructions: r.instructions,
  }
}

export async function searchRecipes(
  request: SearchRequest,
): Promise<SearchResponse> {
  const { data } = await API.post<SearchResponse>('/search', {
    query: request.query,
    filters: request.filters ?? [],
    limit: request.limit,
  })

  return {
    query: data.query,
    total: data.total,
    recipes: data.recipes.map(mapBackendRecipe),
  }
}

export async function fetchSuggestions(query: string): Promise<SearchSuggestion[]> {
  const { data } = await API.get<SearchSuggestion[]>(
    `/search/suggest?query=${encodeURIComponent(query)}`,
  )
  return data
}

export async function fetchCategories(): Promise<CategoryInfo[]> {
  const { data } = await API.get<{ name: string; count: number }[]>(
    '/search/categories',
  )
  return data
}

export async function fetchRecipeById(id: number): Promise<Recipe | undefined> {
  const { data } = await API.get(`/recipes/${id}`)
  return mapBackendRecipe(data)
}

export async function fetchSimilarRecipes(id: number): Promise<Recipe[]> {
  const { data } = await API.get<
    {
      id: number
      title: string
      description: string
      image: string
      categories: string[]
      cookTimeMinutes: number
      servings: number
      ingredients: { name: string; amount: string }[]
      instructions: { step: number; description: string }[]
    }[]
  >(`/recipes/${id}/similar`)
  return data.map(mapBackendRecipe)
}
