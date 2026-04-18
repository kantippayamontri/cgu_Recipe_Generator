import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { Recipe } from '../types/recipe.ts'

interface RecipeCardProps {
  recipe: Recipe
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const [isBookmarked, setIsBookmarked] = useState(false)

  return (
    <article className="group relative overflow-hidden rounded-[2rem] bg-surface shadow-[0_24px_70px_-42px_rgba(59,57,13,0.48)] ring-1 ring-outline-variant/35 transition duration-300 hover:-translate-y-1">
      <button
        type="button"
        aria-label={isBookmarked ? 'Remove bookmark' : 'Save recipe'}
        onClick={() => setIsBookmarked((currentValue) => !currentValue)}
        className="absolute right-4 top-4 z-10 flex h-11 w-11 items-center justify-center rounded-full bg-surface/85 text-on-surface shadow-sm backdrop-blur transition hover:bg-surface"
      >
        <span className="material-symbols-outlined">
          {isBookmarked ? 'bookmark' : 'bookmark_add'}
        </span>
      </button>

      <Link to={`/recipes/${recipe.id}`} className="block h-full">
        <img
          src={recipe.image}
          alt={recipe.title}
          className="h-60 w-full object-cover transition duration-500 group-hover:scale-[1.02]"
        />

        <div className="space-y-4 p-5">
          <div className="flex flex-wrap gap-2">
            {recipe.categories.slice(0, 2).map((category) => (
              <span
                key={category}
                className="rounded-full bg-secondary-container px-3 py-1 text-xs font-semibold uppercase tracking-wide text-secondary"
              >
                {category}
              </span>
            ))}
          </div>

          <div className="space-y-2">
            <h3 className="text-2xl font-extrabold tracking-tight text-on-surface">
              {recipe.title}
            </h3>
            <p className="line-clamp-2 text-sm leading-6 text-on-surface-variant">
              {recipe.description}
            </p>
          </div>

          <div className="flex items-center gap-4 text-sm text-on-surface-variant">
            <span>{recipe.cookTimeMinutes} min</span>
            <span>{recipe.ingredients.length} ingredients</span>
            <span>{recipe.servings} servings</span>
          </div>
        </div>
      </Link>
    </article>
  )
}
