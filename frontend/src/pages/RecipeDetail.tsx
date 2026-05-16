import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { RecipeCard } from '../components/RecipeCard.tsx'
import { fetchRecipeById, fetchSimilarRecipes } from '../lib/api.ts'

export function RecipeDetail() {
  const { id } = useParams<{ id: string }>()
  const recipeId = Number(id)
  const [checkedIngredients, setCheckedIngredients] = useState<string[]>([])
  const [imageStatus, setImageStatus] = useState<'loading' | 'loaded' | 'error'>('loading')

  useEffect(() => {
    const timer = setTimeout(() => {
      setImageStatus((s) => (s === 'loading' ? 'error' : s))
    }, 5000)
    return () => clearTimeout(timer)
  }, [])
  const { data: recipe, isLoading } = useQuery({
    queryKey: ['recipe', recipeId],
    queryFn: () => fetchRecipeById(recipeId),
    enabled: Number.isFinite(recipeId),
  })
  const { data: similarRecipes = [] } = useQuery({
    queryKey: ['similar-recipes', recipeId],
    queryFn: () => fetchSimilarRecipes(recipeId),
    enabled: Number.isFinite(recipeId),
  })

  if (isLoading) {
    return (
      <main className="mx-auto flex max-w-4xl flex-col items-center gap-4 px-6 py-20 text-center sm:px-8">
        <h1 className="text-4xl font-extrabold tracking-tight">Loading recipe</h1>
        <p className="text-on-surface-variant">
          Pulling the mock recipe details into the gallery.
        </p>
      </main>
    )
  }

  if (!recipe) {
    return (
      <main className="mx-auto flex max-w-4xl flex-col items-center gap-4 px-6 py-20 text-center sm:px-8">
        <h1 className="text-4xl font-extrabold tracking-tight">Recipe not found</h1>
        <p className="text-on-surface-variant">
          This mock recipe does not exist in the local catalog.
        </p>
        <Link
          to="/search"
          className="rounded-full bg-primary px-5 py-3 font-semibold text-surface"
        >
          Back to search
        </Link>
      </main>
    )
  }

  function handleIngredientToggle(name: string) {
    setCheckedIngredients((currentValue) =>
      currentValue.includes(name)
        ? currentValue.filter((entry) => entry !== name)
        : [...currentValue, name],
    )
  }

  return (
    <main className="pb-16">
      <section className="mx-auto grid max-w-7xl gap-10 px-6 py-10 sm:px-8 lg:grid-cols-[1.15fr_0.85fr] lg:px-10 lg:py-14">
        <div className="space-y-6">
          <div className="flex flex-wrap gap-3">
            {recipe.categories.map((category) => (
              <span
                key={category}
                className="rounded-full bg-secondary-container px-4 py-2 text-sm font-semibold text-secondary"
              >
                {category}
              </span>
            ))}
          </div>

          <div className="space-y-6">
            <div className="space-y-4">
              <h1 className="text-5xl font-extrabold tracking-[-0.04em] sm:text-6xl">
                {recipe.title}
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-on-surface-variant">
                {recipe.description}
              </p>
            </div>

            <div className="flex flex-wrap gap-3 text-sm text-on-surface-variant">
              <div className="rounded-full bg-surface-container px-4 py-2">
                {recipe.cookTimeMinutes} minutes
              </div>
              <div className="rounded-full bg-surface-container px-4 py-2">
                {recipe.servings} servings
              </div>
              <div className="rounded-full bg-surface-container px-4 py-2">
                {recipe.ingredients.length} ingredients
              </div>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-[2rem] bg-surface-container p-4 shadow-[0_30px_100px_-60px_rgba(59,57,13,0.75)]">
          {imageStatus === 'loading' && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-outline-variant border-t-primary" />
            </div>
          )}
          <img
            src={imageStatus === 'error' ? 'https://img.magnific.com/premium-vector/file-folder-mascot-character-design-vector_166742-4413.jpg?semt=ais_hybrid&w=740&q=80' : recipe.image}
            alt={recipe.title}
            onLoad={() => setImageStatus((s) => (s === 'error' ? 'error' : 'loaded'))}
            onError={() => setImageStatus('error')}
            className={`h-full min-h-[320px] w-full rounded-[1.5rem] object-cover transition duration-500 ${imageStatus === 'loading' ? 'invisible' : ''}`}
          />
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-8 px-6 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:px-10">
        <div className="rounded-[2rem] bg-surface-container-low p-6">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-3xl font-extrabold tracking-tight">Ingredients</h2>
            <p className="text-sm text-on-surface-variant">
              {checkedIngredients.length}/{recipe.ingredients.length} checked
            </p>
          </div>

          <div className="mt-6 space-y-3">
            {recipe.ingredients.map((ingredient) => {
              const isChecked = checkedIngredients.includes(ingredient.name)

              return (
                <button
                  key={ingredient.name}
                  type="button"
                  onClick={() => handleIngredientToggle(ingredient.name)}
                  className={`flex w-full items-center justify-between rounded-[1.5rem] px-4 py-4 text-left transition ${
                    isChecked
                      ? 'bg-secondary-container text-secondary'
                      : 'bg-surface text-on-surface'
                  }`}
                >
                  <span className="font-semibold capitalize">{ingredient.name}</span>
                  <span className="text-sm opacity-80">{ingredient.amount}</span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="rounded-[2rem] bg-surface p-6 shadow-[0_24px_70px_-48px_rgba(59,57,13,0.45)] ring-1 ring-outline-variant/35">
          <h2 className="text-3xl font-extrabold tracking-tight">Instructions</h2>
          <div className="mt-6 space-y-5">
            {recipe.instructions.map((instruction) => (
              <div key={instruction.step} className="flex gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary font-bold text-surface">
                  {instruction.step}
                </div>
                <p className="pt-2 text-base leading-7 text-on-surface-variant">
                  {instruction.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto mt-10 max-w-7xl space-y-6 px-6 sm:px-8 lg:px-10">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-secondary">
              Similar recipes
            </p>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight">
              Keep the menu going
            </h2>
          </div>
          <Link to="/search" className="text-sm font-semibold text-primary">
            View all recipes
          </Link>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {similarRecipes.map((similarRecipe) => (
            <RecipeCard key={similarRecipe.id} recipe={similarRecipe} />
          ))}
        </div>
      </section>
    </main>
  )
}
