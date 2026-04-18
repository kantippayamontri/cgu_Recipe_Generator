interface FilterSidebarProps {
  available: string[]
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
      {available.map((category) => {
        const isActive = active.includes(category)

        return (
          <button
            key={category}
            type="button"
            onClick={() => onChange(category)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              isActive
                ? 'bg-primary text-surface shadow-[0_20px_45px_-32px_rgba(157,79,0,0.95)]'
                : 'bg-surface text-on-surface-variant ring-1 ring-outline-variant/55 hover:bg-surface-container-low'
            }`}
          >
            {category}
          </button>
        )
      })}
    </div>
  )
}
