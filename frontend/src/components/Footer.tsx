export function Footer() {
  return (
    <footer className="bg-surface-container-low">
      <div className="h-1 bg-gradient-to-r from-primary via-secondary to-primary" />
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-6 py-8 sm:flex-row sm:items-center sm:px-8 lg:px-10">
        <div className="flex flex-col gap-1">
          <p className="font-extrabold text-on-surface">Bite-Sized Magic</p>
          <p className="text-sm text-on-surface-variant">
            Discover recipe ideas from your pantry
          </p>
        </div>
        <div className="flex flex-col gap-1 text-right">
          <p className="text-sm font-medium text-on-surface">Created by</p>
          <p className="text-sm text-on-surface-variant">Kan Tippayamontri M1461023</p>
        </div>
      </div>
    </footer>
  )
}
