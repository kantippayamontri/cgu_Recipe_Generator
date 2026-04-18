# The Culinary Gallery Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the frontend inside `frontend/` to match the approved Stitch screens using mock data instead of the unfinished backend.

**Architecture:** Scaffold a Vite React TypeScript app, add Tailwind design tokens from Stitch, build shared components and three routed pages, and power them with typed mock data through simple React Query hooks. Keep an axios API client scaffolded but unused so the eventual backend migration is small.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Axios

---

## File Map

- Create `frontend/` Vite app scaffold
- Create `frontend/src/types/recipe.ts` for typed UI models
- Create `frontend/src/lib/mockData.ts` for typed recipes and suggestions
- Create `frontend/src/lib/api.ts` for inactive API helpers
- Create `frontend/src/hooks/useSearch.ts` and `frontend/src/hooks/useSuggestions.ts`
- Create `frontend/src/components/Navbar.tsx`, `Footer.tsx`, `SearchBar.tsx`, `RecipeCard.tsx`, `FilterSidebar.tsx`
- Create `frontend/src/pages/Home.tsx`, `SearchResults.tsx`, `RecipeDetail.tsx`
- Modify `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/index.html`, `frontend/tailwind.config.js`, `frontend/src/index.css`

## Task 1: Scaffold frontend app

- [ ] Run `npm create vite@latest . -- --template react-ts` in `frontend/`
- [ ] Install runtime dependencies: `react-router-dom`, `@tanstack/react-query`, `axios`
- [ ] Install styling dependencies: `tailwindcss`, `postcss`, `autoprefixer`
- [ ] Initialize Tailwind with `npx tailwindcss init -p`
- [ ] Verify the default app boots with `npm run dev`

## Task 2: Apply Stitch design system

- [ ] Replace Tailwind config with the Stitch color, font, and radius tokens
- [ ] Update `src/index.css` with Tailwind directives and shared base styles
- [ ] Add Google Fonts and Material Symbols links to `index.html`
- [ ] Verify a simple primary headline renders with the correct fonts and colors

## Task 3: Add types and mock data layer

- [ ] Create typed recipe models in `src/types/recipe.ts`
- [ ] Create `src/lib/mockData.ts` with 8 recipes, suggestions, and categories
- [ ] Create `src/lib/api.ts` with TODO-marked real API calls for later
- [ ] Create `useSearch` and `useSuggestions` hooks that read mock data client-side
- [ ] Run `npx tsc --noEmit`

## Task 4: Build shared UI components

- [ ] Create `Navbar.tsx` and `Footer.tsx` from the Stitch shell
- [ ] Create `RecipeCard.tsx` with navigation and bookmark button
- [ ] Create `SearchBar.tsx` with suggestion dropdown behavior
- [ ] Create `FilterSidebar.tsx` as a chip row component
- [ ] Run `npx tsc --noEmit`

## Task 5: Build pages and app shell

- [ ] Create `Home.tsx` with hero, search, chips, and recipe grid
- [ ] Create `SearchResults.tsx` with URL-driven results and removable chips
- [ ] Create `RecipeDetail.tsx` with checklist ingredients, instructions, and similar recipes
- [ ] Wire routes and providers in `App.tsx` and `main.tsx`
- [ ] Run `npx tsc --noEmit`
- [ ] Run `npm run build`
- [ ] Smoke test `/`, `/search`, and `/recipes/:id`

## Verification

- `cd frontend && npx tsc --noEmit`
- `cd frontend && npm run build`

## Self-review

- Spec coverage: all three Stitch screens, mock-first data flow, shared shell, and AGENTS.md file structure are covered
- Placeholder scan: no TODO-style implementation gaps except the intentional future backend swap note in `api.ts`
- Type consistency: plan uses one shared `Recipe` model across components, pages, hooks, and mock data
