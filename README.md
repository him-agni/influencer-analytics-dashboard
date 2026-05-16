# 📊 Influencer Analytics Dashboard

YouTube channel analytics — collect data, analyze sentiment, score influence, all from a premium Web UI.

## 🆓 Cost: Everything is FREE

| Component | Cost | Details |
|-----------|------|---------|
| **YouTube Data API v3** | Free | 10,000 units/day (Google Cloud) |
| **Sentiment Analysis** | Free | HuggingFace DistilBERT runs locally |
| **PostgreSQL** | Free | Local install or Docker |
| **Python + FastAPI** | Free | Open source |

---

## 🔑 YouTube API Key Setup (FREE, 5 minutes)

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"NEW PROJECT"**
3. Name it `influencer-analytics` → Click **Create**

### Step 2: Enable YouTube Data API
1. Go to **APIs & Services** → **Library**
2. Search for **"YouTube Data API v3"**
3. Click it → Click **"ENABLE"**

### Step 3: Create an API Key
1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"API Key"**
3. Copy the key
4. Paste it in your `.env` file: `YOUTUBE_API_KEY=your_key_here`

### API Quota (Free Tier)
- **10,000 units/day** — resets daily at midnight Pacific Time
- Channel lookup: ~3 units
- Video list (50 videos): ~100 units
- Comments (100 per video): ~5 units per video
- **One full channel scan ≈ 130 units** → ~75 channels/day

---

## 🐘 PostgreSQL Setup

### Option A: Install Locally
1. Download from [postgresql.org/download](https://www.postgresql.org/download/)
2. Install with default settings (remember your password!)
3. Create the database:
```sql
CREATE DATABASE influencer_db;
```

### Option B: Docker (recommended)
```bash
docker run --name pg-influencer -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=influencer_db -p 5432:5432 -d postgres:16
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
#    Edit .env with your YouTube API key and PostgreSQL credentials

# 3. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Open the dashboard
#    http://localhost:8000
```

---

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py           # SQLAlchemy async setup
│   ├── core/                 # Config & logging
│   ├── models/               # ORM models (6 tables)
│   ├── schemas/              # Pydantic schemas
│   ├── api/v1/               # REST endpoints
│   ├── services/             # YouTube collector, sentiment, scoring
│   ├── repositories/         # Database CRUD
│   └── scheduler/            # APScheduler background jobs
├── frontend/                 # Web UI (HTML/CSS/JS)
├── requirements.txt
├── .env                      # Your config (not committed)
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/collect` | Collect YouTube channel data |
| GET | `/api/v1/dashboard` | Dashboard summary |
| GET | `/api/v1/profiles` | List all profiles |
| GET | `/api/v1/profiles/{id}` | Profile detail |
| GET | `/api/v1/profiles/{id}/posts` | Videos list |
| GET | `/api/v1/profiles/{id}/growth` | Growth history |
| GET | `/api/v1/profiles/{id}/engagement` | Engagement metrics |
| GET | `/api/v1/profiles/{id}/hashtags` | Top hashtags |
| GET | `/api/v1/profiles/{id}/comments` | Comments |
| GET | `/api/v1/profiles/{id}/sentiment` | Sentiment analysis |
| GET | `/api/v1/profiles/{id}/score` | Influence score |
| GET | `/api/health` | Health check |

Interactive API docs: `http://localhost:8000/docs`

## 📊 Power BI Connection

1. Open Power BI Desktop → **Get Data** → **PostgreSQL database**
2. Server: `localhost`, Database: `influencer_db`
3. Select **DirectQuery** for live data
4. Choose tables and build your reports!
