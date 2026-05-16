# Deployment Instructions

## Prerequisites

- Docker & Docker Compose installed on VPS
- `data/process/recipes_tfidf_ready.csv` present (run the preprocessing pipeline if missing)
- nginx proxy manager set up on the VPS (or any reverse proxy)

## Ports

| Container | Host Port | Internal Port |
|-----------|-----------|---------------|
| backend   | `2222`    | `8000`        |
| frontend  | `2223`    | `3000`        |

## Setup

### 1. Clone & prepare data

```bash
git clone <repo-url>
cd cgu_Recipe_Generator

# Ensure the processed data file exists
ls -lh data/process/recipes_tfidf_ready.csv
# If missing, run: uv run python -m data_preprocessing.full_preprocess
```

### 2. Set your API domain

Replace `api.yourdomain.com` with your actual API subdomain:

```bash
export VITE_API_URL=https://api.yourdomain.com/api/v1
```

### 3. Build & start

```bash
# First deploy
docker compose up -d --build

# Subsequent deploys (after code changes)
docker compose up -d --build

# Restart without rebuilding
docker compose up -d

# Stop everything
docker compose down
```

### 4. Configure nginx proxy manager

| Proxy Host            | Scheme | Forward Host | Forward Port |
|-----------------------|--------|-------------|---------------|
| `api.yourdomain.com`  | http   | VPS_IP      | `2222`        |
| `app.yourdomain.com`  | http   | VPS_IP      | `2223`        |

Enable **WebSocket support** and **Force SSL** for both hosts.

### 5. Verify

```bash
# Backend health
curl https://api.yourdomain.com/api/v1/health

# Search
curl -X POST https://api.yourdomain.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"tomato","limit":3}'

# Frontend
curl -I https://app.yourdomain.com/
```

Open `https://app.yourdomain.com` in a browser and search for a recipe.

## Updating

```bash
git pull
export VITE_API_URL=https://api.yourdomain.com/api/v1
docker compose up -d --build
```

## Troubleshooting

### Backend fails to start

```bash
docker compose logs backend
```

Common causes:
- `recipes_tfidf_ready.csv` missing — run the preprocessing pipeline
- Port conflict — check nothing else uses port 2222

### Frontend can't reach API

- Verify `VITE_API_URL` was set correctly during build: check browser devtools Network tab
- Ensure nginx proxy manager routes are active and SSL certificates are valid
- Check CORS response headers — should show `Access-Control-Allow-Origin: *`

### Rebuild a single service

```bash
docker compose up -d --build backend   # only rebuild backend
docker compose up -d --build frontend  # only rebuild frontend
```
