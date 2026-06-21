# Blue Grid

**Predicting urban water infrastructure failures before they happen**

Built with Claude Code for UC Berkeley AI Hackathon 2026 (Anthropic Prize Track)

---

## What This Is

Blue Grid is a civic water-infrastructure risk dashboard that uses **real failure data** from the City of Kitchener to predict where the next water main break will occur. It's not speculative — Kitchener logs every break it has ever had, so we trained on real failures, validated against held-out breaks, and turned it into a command center that tells the city exactly where to inspect next.

**One-line pitch:** The city logs every water main break → we trained on real failures → validated model → command center for targeted inspections.

---

## Live Demo

**Fastest way (Mac):** Double-click `start_demo.command` to launch everything.

**Or run manually:**
```bash
./start_demo.command
```

**Or minimal (dashboard only):**
```bash
python3 -m http.server 8000
# Then open http://localhost:8000/landing.html
```

---

## Features

### Core Dashboard
- **138 zones** across Kitchener with real lat/lon coordinates
- **488 historical breaks** analyzed from city data
- **27 critical zones** identified (risk 81-100)
- **Validated model**: ranks 73% of streets that actually broke in the top quartile
- **Transparent risk scoring**: age (35%) + material (25%) + break history (25%) + flood (15%)
- Interactive map with color-coded risk levels
- Neighborhood-friendly names (Downtown Kitchener, Bridgeport, etc.)
- Click-to-explain panels with factor breakdowns

### Sponsor Integrations (All Live)

**🤖 Anthropic (Claude)**
- "Generate Action Plan" button calls Claude API
- Sends real zone data (risk, age, material, breaks)
- Returns structured 72-hour operational plan
- Three sections: Immediate, 72-Hour, Long-Term actions

**🔴 Redis (Vector Search)**
- Semantic similarity search over historical breaks
- 384-dim embeddings using sentence transformers
- COSINE distance K-NN search
- Shows "Similar Past Failures" for any selected zone
- Demonstrates Redis as vector database, not just cache

**🌐 Browserbase (Ingestion)**
- Automated agent scrapes latest break data
- Runs in cloud headless browser
- Compatible output format for pipeline
- Enables continuous data updates

---

## Quick Start

### 🚀 One-Command Demo Launch (Recommended)

**Mac users:** Double-click `start_demo.command` in Finder, or:
```bash
./start_demo.command
```

This will:
- ✓ Start web server on port 8000
- ✓ Start Anthropic API proxy on port 5002
- ✓ Start Redis vector search API on port 5001
- ✓ Open browser to http://localhost:8000
- ✓ Display all service logs

**To stop all services:**
```bash
./stop_demo.sh
```

Or just press `Ctrl+C` in the terminal running `start_demo.command`.

---

### Manual Setup (Alternative)

### 1. Core Dashboard (No setup needed)
```bash
python3 -m http.server 8000
# Open http://localhost:8000/landing.html
```

### 2. Enable Claude Action Plans
```bash
# Add your Anthropic API key to config.json
{
  "anthropicApiKey": "sk-ant-your-key-here"
}

# Start the proxy
python3 anthropic_proxy.py
```
See **API_SETUP.md** for details.

### 3. Enable Redis Vector Search
```bash
# Install Redis
brew install redis
brew services start redis

# Install dependencies
pip install redis sentence-transformers flask flask-cors

# Setup and run
python setup_redis.py
python redis_api.py
```
See **SPONSOR_INTEGRATIONS.md** for details.

### 4. Run Browserbase Agent
```bash
# Add Browserbase API key to config.json
{
  "browserbaseApiKey": "bb_your-key-here"
}

# Install and run
pip install browserbase playwright
playwright install chromium
python browserbase_agent.py
```

---

## Project Structure

```
bluegrid/
├── landing.html              — Premium entry page
├── index.html                — Interactive dashboard
├── zones.json                — 138 Kitchener zones (validated data)
│
├── build_data.py             — Data pipeline (mains + breaks → zones)
├── setup_redis.py            — Redis vector index setup
├── redis_api.py              — Similarity search API
├── browserbase_agent.py      — Automated ingestion
│
├── config.json               — API keys (gitignored)
├── requirements.txt          — Python dependencies
│
├── README.md                 — This file
├── API_SETUP.md              — Anthropic setup
├── SPONSOR_INTEGRATIONS.md   — Redis + Browserbase guide
└── CLAUDE.md                 — Project context
```

---

## The Honest Framing

We **DO NOT** claim to predict the exact pipe and hour of a break.

We **DO** produce:
- A validated, transparent, zone-level risk ranking
- Real data from City of Kitchener's public records
- A model that ranks 73% of streets that actually broke in the top quartile
- Actionable insights for city operations teams

**Directional + validated + honest beats over-claimed accuracy.**

---

## Technical Stack

**Frontend:**
- Single-file HTML (no build step)
- Leaflet + OpenStreetMap
- Dark command-center theme
- Real-time API calls (Claude, Redis)

**Backend:**
- Python data pipeline (geopandas, scikit-learn)
- Flask API for Redis vector search
- Browserbase for web scraping

**Data Sources:**
- City of Kitchener Open Data (ArcGIS FeatureServer)
- Water Mains asset inventory
- Water Main Breaks historical records

**Sponsor Technologies:**
- Anthropic Claude (action plan generation)
- Redis (vector similarity search)
- Browserbase (automated data ingestion)

---

## Validation

Three verification checks (all passing):

1. **[VERIFY 1] Bounding Box**
   ```
   lon -80.563 to -80.386, lat 43.371 to 43.500
   OK — contains Kitchener center
   ```

2. **[VERIFY 2] Break Matches**
   ```
   488 of 2000 breaks snapped to segments
   OK — spatial join succeeded
   ```

3. **[VERIFY 3] Model Performance**
   ```
   ROC-AUC: 0.693
   Top-quartile capture: 73%
   ```

---

## Installation

**All dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

**Or individually:**
```bash
# Core pipeline
pip install geopandas pandas scikit-learn shapely numpy requests

# Redis vector search
pip install redis sentence-transformers flask flask-cors

# Browserbase agent
pip install browserbase playwright anthropic
```

---

## Data Pipeline

```bash
# Pull data, score zones, train model, export
python build_data.py
```

**What it does:**
1. Schema check (verify field names)
2. Pull full mains + breaks from ArcGIS
3. Reproject to EPSG:4326, verify bounding box
4. Spatial join (break → nearest main)
5. Transparent risk scoring
6. Random Forest validation
7. Export zones.json

**Output:** zones.json (138 zones, validated)

---

## API Endpoints

**Redis Similarity Search (port 5001):**
```
POST /api/similar-breaks
GET  /api/health
```

**Usage:**
```bash
curl -X POST http://localhost:5001/api/similar-breaks \
  -H "Content-Type: application/json" \
  -d '{"age": 60, "material": 100, "breaks": 10}'
```

---

## Documentation

- **README.md** (this file) — Project overview
- **API_SETUP.md** — Anthropic Claude setup
- **SPONSOR_INTEGRATIONS.md** — Redis + Browserbase (detailed)
- **CLAUDE.md** — Full project context

---

## Credits

**Built with:**
- Claude Code (Anthropic)
- City of Kitchener Open Data
- Redis, Browserbase (sponsor integrations)
- Leaflet, sentence-transformers

**For:**
- UC Berkeley AI Hackathon 2026
- Anthropic Prize Track

**Solo build, Sunday 11am deadline**

---

## License

MIT (for demo/educational purposes)

Data: City of Kitchener Open Data Portal (public)
