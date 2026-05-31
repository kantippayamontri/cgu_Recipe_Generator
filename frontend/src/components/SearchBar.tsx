import { useState } from 'react'
import type { FormEvent } from 'react'

import { useSuggestions } from '../hooks/useSuggestions.ts'

interface SearchBarProps {
  initialQuery?: string
  onSearch: (query: string) => void
  placeholder?: string
}

export function SearchBar({
  initialQuery = '',
  onSearch,
  placeholder = 'Search recipes, ingredients, or ideas',
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)
  const [isOpen, setIsOpen] = useState(false)
  const { data: suggestions = [] } = useSuggestions(query)

  function submitSearch(value: string) {
    const trimmedValue = value.trim()
    onSearch(trimmedValue)
    setIsOpen(false)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submitSearch(query)
  }

  return (
    <div className="relative w-full">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 rounded-full bg-surface px-3 py-3 shadow-[0_24px_70px_-40px_rgba(59,57,13,0.45)] ring-1 ring-outline-variant/40"
      >
        <span className="material-symbols-outlined ml-2 text-on-surface-variant">
          search
        </span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => setIsOpen(true)}
          onBlur={() => window.setTimeout(() => setIsOpen(false), 120)}
          placeholder={placeholder}
          className="min-w-0 flex-1 border-none bg-transparent text-base text-on-surface outline-none placeholder:text-on-surface-variant/80"
        />
        <button
          type="submit"
          className="rounded-full bg-primary px-5 py-3 text-sm font-semibold text-surface transition hover:opacity-90"
        >
          Search
        </button>
      </form>

      {isOpen && suggestions.length > 0 ? (
        <div className="absolute inset-x-0 top-[calc(100%+0.75rem)] z-20 overflow-hidden rounded-[1.75rem] bg-surface shadow-[0_24px_80px_-35px_rgba(59,57,13,0.45)] ring-1 ring-outline-variant/40">
          {suggestions.slice(0, 5).map((suggestion) => (
            <button
              key={suggestion.text}
              type="button"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                setQuery(suggestion.text)
                submitSearch(suggestion.text)
              }}
              className="flex w-full items-center justify-between px-5 py-4 text-left text-sm text-on-surface transition hover:bg-surface-container-low"
            >
              <span className="truncate">{suggestion.text}</span>
              <span className="ml-2 shrink-0 rounded-full bg-surface-container-highest px-2 py-0.5 text-xs font-medium text-on-surface-variant">
                {suggestion.source}
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
