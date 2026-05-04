import type { CategoryInfo } from '../types/recipe.ts'

interface FilterSidebarProps {
  available: CategoryInfo[]
  active: string[]
  onChange: (category: string) => void
}

export function FilterSidebar({
  available,
  active,
  onChange,
}: FilterSidebarProps) {
  return (
    <div className="flex flex-wrap gap-3">
      {available.map(({ name, count }) => {
        const isActive = active.includes(name)

        return (
          <button
            key={name}
            type="button"
            onClick={() => onChange(name)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              isActive
                ? 'bg-primary text-surface shadow-[0_20px_45px_-32px_rgba(157,79,0,0.95)]'
                : 'bg-surface text-on-surface-variant ring-1 ring-outline-variant/55 hover:bg-surface-container-low'
            }`}
          >
            {name}
            <span className="ml-1 font-normal opacity-55">{count}</span>
          </button>
        )
      })}
    </div>
  )
}