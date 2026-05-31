import { useQuery } from '@tanstack/react-query'

import { fetchSuggestions } from '../lib/api.ts'
import type { SearchSuggestion } from '../types/recipe.ts'

export function useSuggestions(query: string) {
  return useQuery<SearchSuggestion[]>({
    queryKey: ['suggestions', query],
    queryFn: () => fetchSuggestions(query),
  })
}
