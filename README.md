# 📱 Egypt Phone Prices

A production-ready system that scrapes, aggregates, and tracks smartphone prices from Egyptian retailers — with historical price tracking, brand/spec data from GSMArena, and a full Next.js frontend.

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Next.js Frontend (Vercel)                        │
│  - Device listing, price comparison, charts       │
└───────────────┬──────────────────────────────────┘
                │ REST API
┌───────────────▼──────────────────────────────────┐
│  FastAPI Backend (Railway / Vercel Functions)     │
│  - /devices, /prices, /trends, /admin             │
└───────────────┬──────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────┐
│  PostgreSQL (Supabase / Neon)                     │
│  brands → devices → retailers → prices            │
└──────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────┐
│  Scrapling Spiders + Celery Beat (Railway)        │
│  GSMArena metadata + Jumia/Noon/BTech/Amazon.eg   │
└──────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/SamoTech/egypt-phone-prices
cd egypt-phone-prices

# 2. Backend
cd backend
cp ../.env.example .env   # fill in values
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. Worker (separate terminal)
celery -A app.tasks.celery_app worker -l info
celery -A app.tasks.celery_app beat  -l info

# 4. Frontend
cd ../frontend
cp ../.env.example .env.local  # fill NEXT_PUBLIC_API_URL
npm install && npm run dev
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full Vercel + Railway + Supabase setup.
