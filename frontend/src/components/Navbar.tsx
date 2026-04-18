import { Link } from 'react-router-dom'

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-outline-variant/40 bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 sm:px-8 lg:px-10">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-primary text-lg font-extrabold text-surface">
            CG
          </span>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-secondary">
              Culinary Gallery
            </p>
            <p className="text-sm text-on-surface-variant">
              Discover recipe ideas from your pantry
            </p>
          </div>
        </Link>

        <nav className="flex items-center gap-3 text-sm font-semibold text-on-surface-variant">
          <Link
            to="/"
            className="rounded-full px-4 py-2 transition hover:bg-surface-container"
          >
            Home
          </Link>
          <Link
            to="/search"
            className="rounded-full bg-primary px-5 py-2.5 text-surface shadow-[0_20px_45px_-30px_rgba(157,79,0,0.9)] transition hover:opacity-90"
          >
            Explore recipes
          </Link>
        </nav>
      </div>
    </header>
  )
}
