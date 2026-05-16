import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import heroImage from '../assets/kan_mascot.webp'
import { FilterSidebar } from '../components/FilterSidebar.tsx'
import { RecipeCard } from '../components/RecipeCard.tsx'
import { SearchBar } from '../components/SearchBar.tsx'
import { useSearch } from '../hooks/useSearch.ts'
import { fetchCategories } from '../lib/api.ts'

interface HomeProps {
  activeFilters?: string[]
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

export function Home({ activeFilters = [] }: HomeProps) {
  const navigate = useNavigate()
  const { data } = useSearch({ query: '', filters: activeFilters, limit: 6 })
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories,
  })

  const featuredRecipes = data?.recipes ?? []

  function handleFilterChange(category: string) {
    const nextFilters = activeFilters.includes(category)
      ? activeFilters.filter((value) => value !== category)
      : [...activeFilters, category]

    navigate(buildSearchPath('', nextFilters))
  }

  return (
    <>
      <section className="mx-auto grid max-w-7xl gap-10 px-6 py-10 sm:px-8 lg:grid-cols-[1.1fr_0.9fr] lg:px-10 lg:py-16">
        <div className="space-y-8">
          <div className="space-y-5">
            <h1 className="max-w-2xl text-5xl font-extrabold tracking-[-0.04em] text-on-surface sm:text-6xl">
              Cook from what you crave, discover what you already have.
            </h1>
            <p className="max-w-xl text-lg leading-8 text-on-surface-variant">
              Tell us what you have, and we'll tell you what you can make.
            </p>
          </div>

          <SearchBar
            onSearch={(query) => navigate(buildSearchPath(query, activeFilters))}
          />

          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-on-surface-variant">
              Popular categories
            </p>
            <FilterSidebar
              available={categories}
              active={activeFilters}
              onChange={handleFilterChange}
            />
          </div>
        </div>

        <div className="relative overflow-hidden rounded-[2rem] bg-surface-container p-5 shadow-[0_28px_90px_-45px_rgba(59,57,13,0.55)]">
          <img
            src={heroImage}
            alt="Fresh plated dishes and ingredients"
            className="h-full min-h-[340px] w-full rounded-[1.5rem] object-cover"
          />
          <div className="absolute inset-x-10 bottom-10 rounded-[1.75rem] bg-surface/88 p-6 backdrop-blur">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-secondary">
              Seasonal pick
            </p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight">
              Curated recipes for fast weeknight cooking.
            </h2>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl space-y-6 px-6 pb-16 sm:px-8 lg:px-10">
        <div className="flex items-end justify-between gap-4">
          <div className="space-y-8">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-on-surface-variant">
              Featured recipes
            </p>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight">
              Start with something delicious
            </h2>
          </div>
          <p className="text-sm text-on-surface-variant">
            {featuredRecipes.length} recipes shown
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {featuredRecipes.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      </section>
    </>
  )
}
