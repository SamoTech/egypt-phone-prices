# Deploying to Render

## Services created by render.yaml

| Service | Type | Purpose |
|---|---|---|
| `egypt-phones-api` | Web (Docker) | FastAPI — health + admin trigger endpoints |
| `egypt-phones-worker` | Worker (Docker) | Celery worker + beat (daily scraper) |
| `egypt-phones-redis` | Redis | Celery broker + result backend |

## Step-by-step

### 1. Create a Render account
https://render.com — free tier works for all three services.

### 2. Connect your GitHub repo
Render Dashboard → New → Blueprint → select `SamoTech/egypt-phone-prices`
Render will auto-detect `render.yaml` and create all services.

### 3. Set environment variables
In the Render dashboard, set these on **both** `egypt-phones-api` and `egypt-phones-worker`:

```
SUPABASE_URL          = https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY = eyJhbGc...
PROXY_LIST            = (optional) http://user:pass@host:port,http://...
```

`DATABASE_URL` and `REDIS_URL` are wired automatically via render.yaml.

### 4. Wait for first deploy (~5-8 min)
The Dockerfile installs Playwright + Scrapling browsers on first build.

### 5. Trigger first scrape manually
```
GET https://egypt-phones-api.onrender.com/api/admin/trigger-scrape?full=true
```
This queues the full GSMArena metadata scrape + all retailer prices.
Expect ~20-40 min for first full run (24 brands × ~50 devices each).

### 6. Connect frontend to backend
In Vercel, add env var:
```
BACKEND_URL = https://egypt-phones-api.onrender.com
```
The Next.js API proxy will now forward to your live Render backend instead of Supabase direct.

### 7. Automatic schedule
Celery beat runs:
- **03:00 Cairo** — full scrape (GSMArena metadata + all retailer prices)
- **Every 6 hours** — price-only refresh (faster, skips GSMArena)

## Local dev with Docker Compose
```bash
cd infra/docker
docker compose up -d        # starts postgres + redis
cd ../../backend
pip install -r requirements.txt
python -m scrapling install # install Playwright browsers
uvicorn app.main:app --reload               # API on :8000
celery -A app.tasks.celery_app worker --beat --loglevel=info  # worker
```
