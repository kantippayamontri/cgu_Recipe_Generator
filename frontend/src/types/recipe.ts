export interface Ingredient {
  name: string
  amount: string
}

export interface Instruction {
  step: number
  description: string
}

export interface Recipe {
  id: number
  title: string
  description: string
  image: string
  categories: string[]
  cookTimeMinutes: number
  servings: number
  ingredients: Ingredient[]
  instructions: Instruction[]
}

export interface CategoryInfo {
  name: string
  count: number
}

export interface SearchRequest {
  query: string
  filters?: string[]
  limit?: number
}

export interface SearchResponse {
  query: string
  total: number
  recipes: Recipe[]
}

export interface SearchSuggestion {
  text: string
  source: string
}
