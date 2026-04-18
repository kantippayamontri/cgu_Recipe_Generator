import { useQuery } from '@tanstack/react-query'

import { fetchSuggestions } from '../lib/api.ts'

export function useSuggestions(query: string) {
  return useQuery<string[]>({
    queryKey: ['suggestions', query],
    queryFn: () => fetchSuggestions(query),
  })
}
