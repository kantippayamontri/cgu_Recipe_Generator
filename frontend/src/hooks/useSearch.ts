import { useQuery } from '@tanstack/react-query'

import { searchRecipes } from '../lib/api.ts'
import type { SearchRequest, SearchResponse } from '../types/recipe.ts'

export function useSearch(request: SearchRequest) {
  return useQuery<SearchResponse>({
    queryKey: ['search', request],
    queryFn: () => searchRecipes(request),
  })
}
