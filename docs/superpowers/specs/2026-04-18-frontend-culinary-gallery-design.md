# Design Spec: The Culinary Gallery Frontend UI

**Date:** 2026-04-18  
**Stitch Project:** `1590403951658244129`

## Overview

Build a React + Vite + TypeScript frontend for the recipe search engine that matches the three approved Google Stitch screens. The backend is not ready yet, so the frontend will use typed mock data first and keep the API client scaffolded but unused.

## Routes

| Route | Page | Stitch Screen |
| --- | --- | --- |
| `/` | `Home.tsx` | Home - Culinary Gallery |
| `/search` | `SearchResults.tsx` | Search Results - Culinary Gallery |
| `/recipes/:id` | `RecipeDetail.tsx` | Recipe Details - Culinary Gallery |

## Design System

### Colors

Use the Stitch palette in Tailwind, including:

- `primary: #9d4f00`
- `secondary: #5d6936`
- `surface: #fffbff`
- `surface-container-low: #fffbd8`
- `surface-container: #f9f5cb`
- `surface-container-highest: #efebad`
- `on-surface: #3b390d`
- `on-surface-variant: #686635`
- `secondary-container: #e9f8b6`
- `outline-variant: #bfbc82`

### Typography

- Headline font: Plus Jakarta Sans
- Body and label font: Manrope
- Load both from Google Fonts in `frontend/index.html`

### Shape and Motion

- `DEFAULT: 1rem`, `lg: 2rem`, `xl: 3rem`, `full: 9999px`
- Prefer tonal separation instead of borders
- Use soft ambient shadows and 300ms+ transitions
- Use glassmorphic action buttons where the Stitch screens show them

## Frontend File Structure

```text
frontend/
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── types/
    │   └── recipe.ts
    ├── lib/
    │   ├── api.ts
    │   └── mockData.ts
    ├── hooks/
    │   ├── useSearch.ts
    │   └── useSuggestions.ts
    ├── components/
    │   ├── Navbar.tsx
    │   ├── Footer.tsx
    │   ├── SearchBar.tsx
    │   ├── RecipeCard.tsx
    │   └── FilterSidebar.tsx
    └── pages/
        ├── Home.tsx
        ├── SearchResults.tsx
        └── RecipeDetail.tsx
```

## Types

`src/types/recipe.ts` defines the shared UI model:

- `Ingredient`
- `Instruction`
- `Recipe`
- `SearchRequest`
- `SearchResponse`

## Mock-first Data Flow

The backend is intentionally not used yet.

- `useSearch(query, filters)` filters `mockRecipes` client-side
- `useSuggestions(query)` filters `mockSuggestions` client-side
- `src/lib/api.ts` is created now but left unused with TODO comments for later server integration

## Mock Data Requirements

`src/lib/mockData.ts` should include:

- 8 typed recipes
- realistic recipe titles, categories, times, ingredients, and instructions
- suggestions derived from recipe titles
- lightweight image URLs suitable for local development

## Component Contracts

### `SearchBar.tsx`

- pill-shaped search input
- autocomplete dropdown from `useSuggestions`
- `onSearch(query: string)` callback

### `RecipeCard.tsx`

- accepts a full `Recipe`
- displays category, title, cook time, ingredient count, image
- includes a non-persistent visual bookmark button
- navigates to the recipe detail route on click

### `FilterSidebar.tsx`

- keeps the existing requested filename even though it renders chip filters
- props: `available`, `active`, `onChange`

### Shared shell components

- `Navbar.tsx`
- `Footer.tsx`

## Page Behavior

### Home

- renders the editorial hero section
- shows search bar and popular filter chips
- shows a responsive recipe grid based on mock data
- search submit navigates to `/search`

### Search Results

- reads `q` and `filters` from the URL
- renders result count and active removable chips
- shows a 3-column responsive results grid
- includes loading skeletons while query state resolves

### Recipe Detail

- reads `:id` from the route
- renders hero image, metadata chips, title, ingredients, instructions, similar recipes
- ingredients are interactive client-side checklist items only

## Constraints

- Follow `AGENTS.md` layout and TypeScript rules
- Keep changes minimal and mock-first
- Do not add new features beyond the Stitch screens and requested mock data behavior
