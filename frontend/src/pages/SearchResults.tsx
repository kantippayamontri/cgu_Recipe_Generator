import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { FilterSidebar } from '../components/FilterSidebar.tsx'
import { RecipeCard } from '../components/RecipeCard.tsx'
import { SearchBar } from '../components/SearchBar.tsx'
import { useSearch } from '../hooks/useSearch.ts'
import { fetchCategories } from '../lib/api.ts'

function readFilters(value: string | null): string[] {
  if (!value) {
    return []
  }

  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function buildSearchPath(query: string, activeFilters: string[]): string {
  const params = new URLSearchParams()

  if (query) {
    params.set('q', query)
  }

  if (activeFilters.length > 0) {
    params.set('filters', activeFilters.join(','))
  }

  const queryString = params.toString()
  return queryString ? `/search?${queryString}` : '/search'
}

function LoadingCard() {
  return (
    <div className="overflow-hidden rounded-[2rem] bg-surface animate-pulse ring-1 ring-outline-variant/35">
      <div className="h-60 bg-surface-container" />
      <div className="space-y-4 p-5">
        <div className="flex gap-2">
          <div className="h-7 w-24 rounded-full bg-surface-container" />
          <div className="h-7 w-24 rounded-full bg-surface-container" />
        </div>
        <div className="h-8 w-3/4 rounded-full bg-surface-container" />
        <div className="h-4 w-full rounded-full bg-surface-container" />
        <div className="h-4 w-2/3 rounded-full bg-surface-container" />
      </div>
    </div>
  )
}

export function SearchResults() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const query = searchParams.get('q') ?? ''
  const activeFilters = readFilters(searchParams.get('filters'))
  const { data, isLoading, isFetching } = useSearch({ query, filters: activeFilters, limit: 20 })
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories,
  })

  const recipes = data?.recipes ?? []

  function handleSearch(nextQuery: string) {
    navigate(buildSearchPath(nextQuery, activeFilters))
  }

  function handleToggleFilter(category: string) {
    const nextFilters = activeFilters.includes(category)
      ? activeFilters.filter((value) => value !== category)
      : [...activeFilters, category]

    navigate(buildSearchPath(query, nextFilters))
  }

  return (
    <>
      <section className="mx-auto max-w-7xl space-y-8 px-6 py-10 sm:px-8 lg:px-10">
        <div className="rounded-[2rem] bg-surface-container-low p-6 shadow-[0_26px_90px_-55px_rgba(59,57,13,0.7)]">
          <div className="space-y-6">
            <div className="space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-secondary">
                Search results
              </p>
              <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
                {query ? `Results for "${query}"` : 'Browse all recipes'}
              </h1>
            </div>

            <SearchBar key={query} initialQuery={query} onSearch={handleSearch} />

            <div className="space-y-4">
              <FilterSidebar
                available={categories}
                active={activeFilters}
                onChange={handleToggleFilter}
              />

              {activeFilters.length > 0 ? (
                <div className="flex flex-wrap gap-3">
                  {activeFilters.map((filter) => (
                    <button
                      key={filter}
                      type="button"
                      onClick={() => handleToggleFilter(filter)}
                      className="rounded-full bg-secondary-container px-4 py-2 text-sm font-semibold text-secondary"
                    >
                      {filter} x
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {isLoading || isFetching
            ? Array.from({ length: 6 }, (_, index) => <LoadingCard key={index} />)
            : recipes.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} />)}
        </div>

        {!isLoading && !isFetching && recipes.length === 0 ? (
          <section className="rounded-[2rem] bg-surface-container p-10 text-center">
            <h2 className="text-2xl font-extrabold tracking-tight">
              No recipes matched this search.
            </h2>
            <p className="mt-3 text-on-surface-variant">
              Try a different query or remove a category chip.
            </p>
          </section>
        ) : null}
      </section>
    </>
  )
}
