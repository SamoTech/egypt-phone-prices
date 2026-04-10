# Deployment Guide — Vercel Only

Everything runs on Vercel (+ Supabase for the database).
No Railway. No separate worker server.
The daily scrape job runs via **GitHub Actions cron** (free).

---

## 1. Database — Supabase (free tier)

1. Create a project at https://supabase.com
2. Go to **Settings → Database → Connection String → URI**
3. Copy the two connection strings (async + sync) into your `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://...
   DATABASE_URL_SYNC=postgresql://...
   ```
4. Run migrations once locally:
   ```bash
   cd backend
   pip install -r requirements.txt
   alembic upgrade head
   ```

---

## 2. Backend (FastAPI) → Vercel

The backend is served as a **Vercel Python serverless function** via `backend/api/index.py`.

```bash
cd backend
npm i -g vercel
vercel          # first time: follow prompts, link/create project
vercel --prod   # deploy to production
```

Set these env vars in the **Vercel dashboard** for the backend project:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Supabase async URI |
| `REDIS_URL` | Upstash Redis URL (free at upstash.com) |
| `ADMIN_TOKEN` | A strong random secret |
| `SCRAPLING_STEALTH` | `true` |
| `PROXY_LIST` | Optional comma-separated proxies |

Note the backend URL (e.g. `https://egypt-phones-api.vercel.app`).

---

## 3. Frontend (Next.js) → Vercel

```bash
cd frontend
vercel          # link/create a separate Vercel project
vercel --prod
```

Set in the **frontend** Vercel project:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | Your backend Vercel URL |

---

## 4. Daily Scrape — GitHub Actions cron

The file `.github/workflows/scrape.yml` runs `python -m app.tasks.run_scrape`
every day at **03:00 Cairo time** (01:00 UTC).

Add these **GitHub Secrets** (Settings → Secrets → Actions):

| Secret | Value |
|---|---|
| `DATABASE_URL` | Supabase async URI |
| `REDIS_URL` | Upstash Redis URL |
| `ADMIN_TOKEN` | Same value as Vercel env |
| `PROXY_LIST` | Optional proxies |

You can also trigger the scrape manually:
**GitHub → Actions → Daily Scrape → Run workflow**

---

## 5. CI/CD — Auto-deploy on push

The `.github/workflows/deploy.yml` pipeline:
- Runs tests on every push / PR
- Deploys backend to Vercel on merge to `main`
- Deploys frontend to Vercel on merge to `main`

Add these **GitHub Secrets**:

| Secret | Value |
|---|---|
| `VERCEL_TOKEN` | From vercel.com/account/tokens |
| `VERCEL_ORG_ID` | From `.vercel/project.json` after first deploy |
| `VERCEL_BACKEND_PROJECT_ID` | From backend `.vercel/project.json` |
| `VERCEL_FRONTEND_PROJECT_ID` | From frontend `.vercel/project.json` |
| `BACKEND_URL` | Your backend Vercel URL |

---

## Redis — Upstash (free tier)

Since Vercel serverless functions can’t connect to a local Redis,
use **Upstash** (free 10K requests/day):

1. Create account at https://upstash.com
2. Create a Redis database → copy the `REDIS_URL`
3. Set it in both Vercel env vars and GitHub Secrets

---

## Full stack summary

| Component | Platform | Cost |
|---|---|---|
| Frontend (Next.js) | Vercel | Free |
| Backend (FastAPI) | Vercel Functions | Free |
| Database | Supabase | Free |
| Cache | Upstash Redis | Free |
| Daily scrape job | GitHub Actions | Free |
