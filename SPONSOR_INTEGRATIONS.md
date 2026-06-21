# Blue Grid — Sponsor Integrations

This document covers the **Redis** and **Browserbase** integrations for the Blue Grid project.

---

## 🔴 Redis: Vector Similarity Search

**What it does:** Uses Redis with vector search to find historical break records similar to any selected zone. Demonstrates semantic similarity using embeddings — not just caching.

### Setup

**1. Install Redis**

macOS:
```bash
brew install redis
brew services start redis
```

Ubuntu/Debian:
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

**2. Install Python Dependencies**

```bash
cd ~/Desktop/bluegrid
pip install redis sentence-transformers flask flask-cors numpy
```

**3. Index Break Records**

```bash
python setup_redis.py
```

This will:
- Load all zones from `zones.json`
- Create semantic embeddings for each zone's break profile using `all-MiniLM-L6-v2`
- Store 384-dimensional vectors in Redis
- Create a FLAT vector index with COSINE distance
- Run a test similarity search

Expected output:
```
✓ Connected to Redis at localhost:6379
✓ Loaded 138 zones from zones.json
✓ Created vector index: break_similarity_idx
✓ Stored 72 break records with embeddings in Redis
```

(Only zones with actual breaks are indexed)

**4. Start the Redis API Server**

```bash
python redis_api.py
```

The API will run on **http://localhost:5001** and provide:
- `POST /api/similar-breaks` — Find similar zones
- `GET /api/health` — Health check

**5. Open the Dashboard**

With the Redis API running:
1. Go to http://localhost:8000
2. Click any zone with historical breaks
3. See the **"Similar Past Failures"** section populate with the top 4 most similar zones
4. Each shows: similarity score, risk, break count, age, material

### How It Works

1. **Embedding**: Each zone's attributes (age, material, break count, etc.) are converted to a semantic text description
2. **Vector Storage**: The sentence transformer model creates a 384-dim embedding vector
3. **Indexing**: Redis stores vectors with metadata in a FLAT index
4. **Query**: When you select a zone, the dashboard:
   - Sends the zone profile to the Redis API
   - API creates an embedding for the query
   - Redis performs K-NN vector search with COSINE distance
   - Returns the top 5 most similar zones (excluding self)

### Technical Details

- **Model**: `all-MiniLM-L6-v2` (384 dimensions, ~80MB)
- **Index**: FLAT with COSINE distance metric
- **Query**: K-NN with k=5
- **Filters**: Excludes self-matches, returns only zones with breaks
- **API**: Flask server on port 5001 with CORS enabled

### What Makes This "Beyond Caching"

This isn't just Redis as a cache — it's **semantic vector search**:
- Finds zones that are *semantically similar* (not just exact matches)
- Uses learned embeddings to understand "similar risk profiles"
- Demonstrates Redis as a vector database, not just key-value store
- Enables exploration: "zones like this one broke — watch these too"

---

## 🌐 Browserbase: Automated Data Ingestion

**What it does:** Uses Browserbase's headless browser infrastructure to scrape the latest water main break data from Kitchener's open data portal, providing a continuously updated data ingestion layer.

### Setup

**1. Get API Keys**

- **Browserbase**: https://www.browserbase.com/ → Get API key
- **Anthropic** (optional, for AI extraction): https://console.anthropic.com/

**2. Update config.json**

```json
{
  "anthropicApiKey": "sk-ant-your-key-here",
  "browserbaseApiKey": "bb_your_key_here"
}
```

**3. Install Dependencies**

```bash
pip install browserbase playwright anthropic
playwright install chromium
```

**4. Run the Agent**

```bash
python browserbase_agent.py
```

### What the Agent Does

1. **Creates a Browserbase Session**: Spins up a remote headless browser
2. **Navigates to Kitchener Portal**: Goes to the Water Main Breaks dataset page
3. **Extracts Break Records**:
   - Looks for the data table or API endpoint
   - Parses recent break incidents
   - Extracts: location, date, material, cause, repair status
4. **Saves to JSON**: Outputs `latest_breaks.json` in a format compatible with `build_data.py`

### Output Format

`latest_breaks.json`:
```json
{
  "city": "Kitchener, ON",
  "source": "Browserbase Agent",
  "scraped_at": "2026-06-20T16:30:00",
  "count": 5,
  "breaks": [
    {
      "INCIDENT_DATE": 1718924400000,
      "BREAK_TYPE": "MAIN",
      "geometry": {
        "type": "Point",
        "coordinates": [-80.49, 43.45]
      },
      "ASSET_MATERIAL": "CI",
      "STATUS": "REPAIR COMPLETED",
      "_scraped_at": "2026-06-20T16:30:00",
      "_source": "browserbase_agent"
    }
  ]
}
```

### Continuous Updates

**Scheduled Ingestion (cron example):**

```bash
# Add to crontab: crontab -e
# Run daily at 2 AM
0 2 * * * cd ~/Desktop/bluegrid && python browserbase_agent.py >> ingestion.log 2>&1
```

### Integration with Pipeline

Option 1: **Append to existing data**
```bash
# Merge latest_breaks.json into the main dataset
python merge_breaks.py  # (create this to merge new breaks)
python build_data.py    # Re-run pipeline with updated data
```

Option 2: **Real-time display**
- Modify dashboard to load `latest_breaks.json` separately
- Show "Recent Breaks (Last 30 Days)" section
- Highlight new breaks on the map with a different color

### Why Browserbase?

- **No local browser needed**: Runs in Browserbase's cloud infrastructure
- **Session recording**: Every scrape is recorded and debuggable
- **Anti-detection**: Residential proxies, realistic browser fingerprints
- **Scalable**: Handle multiple concurrent scrapes without local resources
- **Reliable**: Managed infrastructure handles browser updates, dependencies

This agent demonstrates the "continuously updated data layer" — real projects need fresh data, and Browserbase makes it production-ready.

---

## Running All Services Together

**Terminal 1** — HTTP Server (Dashboard):
```bash
cd ~/Desktop/bluegrid
python3 -m http.server 8000
```

**Terminal 2** — Redis API (Vector Search):
```bash
cd ~/Desktop/bluegrid
python redis_api.py
```

**Terminal 3** — Browserbase Agent (Manual/Scheduled):
```bash
cd ~/Desktop/bluegrid
python browserbase_agent.py
```

---

## Demo Flow

1. **Start Redis**: `brew services start redis`
2. **Index Data**: `python setup_redis.py`
3. **Start API**: `python redis_api.py`
4. **Run Agent**: `python browserbase_agent.py` (fetches latest breaks)
5. **Open Dashboard**: http://localhost:8000
6. **Select Zone**: Click a high-risk zone with breaks
7. **See Similar Failures**: Vector search shows 4 most similar past failures
8. **Generate Action Plan**: Claude creates 72-hour operational plan

---

## Troubleshooting

### Redis

**Connection refused:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
```

**Index not found:**
```bash
# Re-run setup
python setup_redis.py
```

### Browserbase

**API key invalid:**
- Check config.json
- Verify key at https://www.browserbase.com/

**Playwright errors:**
```bash
playwright install chromium
```

**Timeout errors:**
- Kitchener portal may be slow or down
- Agent falls back to simulated data for demo

---

## Files

- `setup_redis.py` — Embeds zones and creates Redis vector index
- `redis_api.py` — Flask API for similarity search
- `browserbase_agent.py` — Automated data ingestion
- `config.json` — API keys (gitignored)
- `SPONSOR_INTEGRATIONS.md` — This file

---

## Credits

- **Redis**: Vector search with RediSearch module
- **Browserbase**: Headless browser infrastructure
- **Anthropic**: Claude API for action plan generation
- **Sentence Transformers**: Embedding model (HuggingFace)
