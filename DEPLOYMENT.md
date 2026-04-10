# Deployment Guide

## 1. Database — Supabase (or Neon)

1. Create a project at https://supabase.com (free tier works)
2. Go to Settings → Database → Connection String → URI mode
3. Copy the connection string; set in `.env` as `DATABASE_URL`
4. Run migrations from Railway/local:
   ```bash
   alembic upgrade head
   ```

## 2. Backend + Worker — Railway

1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Init project:
   ```bash
   cd backend
   railway init
   railway add --service redis   # auto-provisions Redis
   ```
4. Set env vars in Railway dashboard (copy from `.env.example`)
5. Create two services from `backend/`:
   - **API service**: start command → `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Worker service**: start command → `celery -A app.tasks.celery_app worker --beat -l info`
6. Deploy:
   ```bash
   railway up
   ```
7. Note the generated Railway domain (e.g. `https://api-xxx.railway.app`)

## 3. Frontend — Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. From `frontend/`:
   ```bash
   vercel
   ```
3. Set env vars in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL` → your Railway API URL
4. Subsequent deploys:
   ```bash
   vercel --prod
   ```

## 4. CI/CD — GitHub Actions

The `.github/workflows/deploy.yml` pipeline:
- Runs tests on every push to `main`
- Deploys backend to Railway
- Deploys frontend to Vercel

Set these GitHub Secrets:
- `RAILWAY_TOKEN`
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

## 5. vercel.json (frontend root)

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "env": {
    "NEXT_PUBLIC_API_URL": "@next_public_api_url"
  }
}
```
