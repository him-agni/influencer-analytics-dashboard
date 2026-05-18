<div align="center">

# 📊 Influencer Analytics Dashboard

**A full-stack YouTube influencer analytics platform — collect channel data, visualize engagement trends, detect anomalies, and benchmark competitors.**

Link- https://web-production-c5d7e8.up.railway.app/

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Railway](https://img.shields.io/badge/Deployed_on-Railway-0B0D0E?logo=railway&logoColor=white)](https://railway.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## ✨ Features

### 📡 Data Collection
- Paste any YouTube channel URL or `@handle` to automatically collect channel stats, videos, comments, and hashtags via the **YouTube Data API v3**

### 📈 Analytics & Visualization
- **Subscriber Growth** — Interactive line chart tracking follower count over time
- **Engagement Metrics** — Track likes, comments, and views with engagement rate calculations
- **Sentiment Analysis** — NLP-powered comment analysis using HuggingFace DistilBERT (optional)
- **Content Categories** — AI-powered pie chart classifying channel content (Fitness, Travel, Tech, etc.)
- **Influence Score** — Composite 0-100 score weighted across 5 factors with tier badges

### 🔍 Anomaly Detection
- **🚀 Viral Spike Detection** — Automatically flags posts exceeding 3× median views
- **📈 Suspicious Growth** — Detects single-day follower jumps >15%
- **📉 Follower Drops** — Flags subscriber losses >5% (possible bot purges)
- **🤖 Fake Follower Heuristics** — Combines growth spikes, drops, and engagement ratios to assess risk level (Low/Medium/High)

### ⚔️ Competitive Analysis
- Compare 3-5 influencers side-by-side
- Benchmark engagement rates against the global database average
- Share-of-Voice analysis across top hashtags

### ⚙️ Automation
- APScheduler runs every 24h to refresh all tracked channels automatically
- Daily growth snapshots build historical trend data over time

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | Async REST API with auto-generated docs |
| **Database** | PostgreSQL + SQLAlchemy | Async ORM with connection pooling |
| **Frontend** | Vanilla HTML/CSS/JS + Chart.js | Glassmorphic dark-theme SPA |
| **Data Source** | YouTube Data API v3 | Channel stats, videos, comments |
| **NLP** | HuggingFace Transformers | DistilBERT sentiment analysis (optional) |
| **Scheduler** | APScheduler | Background data refresh |
| **Deployment** | Railway | Auto-deploy from GitHub |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (local or Docker)
- YouTube Data API key ([free setup guide below](#-youtube-api-key-setup))

### 1. Clone & Install

```bash
git clone https://github.com/him-agni/influencer-analytics-dashboard.git
cd influencer-analytics-dashboard
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/influencer_db
YOUTUBE_API_KEY=your_api_key_here
SCHEDULER_ENABLED=true
SENTIMENT_ENABLED=true
```

### 3. Set Up PostgreSQL

**Option A: Local Install**
```sql
CREATE DATABASE influencer_db;
```

**Option B: Docker** (recommended)
```bash
docker run --name pg-influencer \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=influencer_db \
  -p 5432:5432 -d postgres:16
```

### 4. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — tables are auto-created on first run.

---

## 🔑 YouTube API Key Setup

> Completely **FREE** — takes ~5 minutes.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project → Name it `influencer-analytics`
3. Navigate to **APIs & Services** → **Library**
4. Search **"YouTube Data API v3"** → Click **Enable**
5. Go to **Credentials** → **+ CREATE CREDENTIALS** → **API Key**
6. Copy the key into your `.env` file

### API Quota (Free Tier)
| Operation | Cost | Daily Limit |
|-----------|------|-------------|
| Channel lookup | ~3 units | 10,000 units/day |
| Video list (50 videos) | ~100 units | Resets at midnight PT |
| Comments (100/video) | ~5 units/video | |
| **Full channel scan** | **~130 units** | **~75 channels/day** |

---

## 📁 Project Structure

```
influencer-analytics-dashboard/
├── app/
│   ├── main.py                  # FastAPI entry point + lifespan
│   ├── database.py              # SQLAlchemy async engine + Railway compat
│   ├── core/
│   │   ├── config.py            # Pydantic settings from .env
│   │   └── logging.py           # Centralized logger
│   ├── models/                  # ORM table definitions
│   │   ├── profile.py           # Channel info (subscribers, views, bio)
│   │   ├── post.py              # Video data (views, likes, duration)
│   │   ├── comment.py           # Comments with sentiment scores
│   │   ├── follower_growth.py   # Daily subscriber snapshots
│   │   ├── engagement_metric.py # Aggregated engagement data
│   │   └── hashtag.py           # Post ↔ hashtag mapping
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── api/v1/
│   │   ├── router.py            # Route aggregator (/api/v1)
│   │   ├── collect.py           # POST /collect — data pipeline
│   │   └── profiles.py          # GET endpoints — analytics + compare
│   ├── services/                # Business logic (no DB awareness)
│   │   ├── youtube_collector.py # YouTube API wrapper
│   │   ├── data_transformer.py  # Raw data → DB-ready structures
│   │   ├── sentiment_analyzer.py# HuggingFace NLP (lazy-loaded)
│   │   ├── scoring.py           # Influence score (0-100)
│   │   ├── category_classifier.py # Content category detection
│   │   └── anomaly_detector.py  # Viral spikes + fake followers
│   ├── repositories/            # Database query layer
│   │   ├── profile_repo.py      # Profile + growth CRUD
│   │   └── post_repo.py         # Posts + comments + hashtags
│   └── scheduler/
│       └── jobs.py              # Daily auto-refresh job
├── frontend/
│   ├── index.html               # SPA shell
│   ├── styles.css               # Glassmorphic dark theme
│   └── app.js                   # UI logic + Chart.js charts
├── requirements.txt
├── Procfile                     # Railway/Heroku start command
├── railway.toml                 # Railway deployment config
├── .env.example                 # Environment variable template
└── README.md
```

---

## 🔌 API Reference

Interactive docs available at `http://localhost:8000/docs`

### Data Collection
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/collect` | Collect a YouTube channel's data |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/dashboard` | Dashboard summary (totals + profiles) |
| `GET` | `/api/v1/profiles` | List all tracked influencers |
| `GET` | `/api/v1/profiles/{id}` | Single profile details |
| `GET` | `/api/v1/profiles/{id}/posts` | Videos (sortable by views, likes, date) |
| `GET` | `/api/v1/profiles/{id}/growth` | Subscriber growth history |
| `GET` | `/api/v1/profiles/{id}/engagement` | Engagement rate over time |
| `GET` | `/api/v1/profiles/{id}/hashtags` | Top hashtags by frequency |
| `GET` | `/api/v1/profiles/{id}/categories` | Content category distribution |
| `GET` | `/api/v1/profiles/{id}/sentiment` | Comment sentiment breakdown |
| `GET` | `/api/v1/profiles/{id}/score` | Influence score + breakdown |
| `GET` | `/api/v1/profiles/{id}/anomalies` | Viral spikes, drops, fake follower risk |

### Competitive Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/compare` | Compare multiple influencers side-by-side |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check for deployment monitoring |

---

## 🧠 How the Scoring Works

The **Influence Score (0-100)** is a weighted composite of 5 factors:

| Factor | Weight | Benchmark Range |
|--------|--------|----------------|
| Subscribers | 20% | 1K → 1M |
| Engagement Rate | 30% | 0.5% → 10% |
| Growth Rate | 20% | -5% → +20% |
| Content Consistency | 15% | 1 → 30 posts/month |
| Sentiment | 15% | 30% → 95% positive |

**Tiers:** Elite (80+) · Rising Star (60+) · Growing (40+) · Emerging (20+) · New (<20)

---

## 🚨 Anomaly Detection Logic

| Detection | Trigger | Purpose |
|-----------|---------|---------|
| **Viral Spike** | Views > median × 3.0 | Identify breakout content |
| **Growth Spike** | Subscribers jump >15% in a day | Flag suspicious growth |
| **Follower Drop** | Subscribers drop >5% in a day | Detect bot purges |
| **Fake Follower Risk** | Low engagement + spikes + drops | Combined risk assessment |

---

## 🌐 Deployment (Railway)

This project is configured for one-click Railway deployment:

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Add a **PostgreSQL** database addon
4. Set environment variables: `YOUTUBE_API_KEY`, `SENTIMENT_ENABLED=false`
5. Railway auto-deploys on every `git push`

> **Note:** PyTorch/Transformers are commented out in `requirements.txt` for Railway's size limits. Sentiment analysis runs locally only.

---

## 📊 Power BI Integration

Connect directly to your PostgreSQL database for advanced reporting:

1. Open Power BI Desktop → **Get Data** → **PostgreSQL database**
2. Server: `localhost` · Database: `influencer_db`
3. Select **DirectQuery** for live data
4. Build custom reports from the 6 available tables

---

## 🆓 Cost: Everything is FREE

| Component | Cost | Details |
|-----------|------|---------|
| YouTube Data API v3 | Free | 10,000 units/day |
| Sentiment Analysis | Free | HuggingFace DistilBERT (local) |
| PostgreSQL | Free | Local, Docker, or Railway addon |
| Railway Hosting | Free tier | 500 hours/month |
| Python + FastAPI | Free | Open source |

---

## 📝 License

This project is open source under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ using FastAPI, Chart.js, and the YouTube Data API**

</div>
