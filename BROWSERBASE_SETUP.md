# Browserbase Setup Guide — Blue Grid

## What This Does
The `browserbase_agent.py` uses Browserbase's cloud browser infrastructure to fetch real water main break data from the City of Kitchener's open data portal. This demonstrates genuine Browserbase integration for the Anthropic prize.

## Step 1: Sign Up for Browserbase

1. Go to https://www.browserbase.com/
2. Click "Sign Up" or "Get Started"
3. Use promo code: **STARTERPACK** (if available) for free credits
4. Complete account creation

## Step 2: Get Your API Credentials

### Get API Key
1. Log into Browserbase dashboard
2. Navigate to **Settings** → **API Keys**
3. Click "Create API Key"
4. Copy the key (starts with `bb_live_...`)

### Get Project ID
1. In Browserbase dashboard, go to **Projects**
2. Either use the default project or create a new one
3. Copy the **Project ID** (looks like `proj_abc123...` or a UUID)

## Step 3: Update config.json

Open `/Users/varnikayadav/Desktop/bluegrid/config.json` and replace:

```json
{
  "anthropicApiKey": "your-existing-key",
  "browserbaseApiKey": "bb_live_YOUR_ACTUAL_KEY_HERE",
  "browserbaseProjectId": "your-actual-project-id",
  "redis_url": "your-existing-redis-url"
}
```

## Step 4: Install Dependencies

Run these commands in your terminal:

```bash
cd /Users/varnikayadav/Desktop/bluegrid

# Install Python packages
pip install browserbase playwright

# Install Playwright browser binaries
playwright install chromium
```

## Step 5: Run the Agent

**Exact command for judges:**

```bash
python3 browserbase_agent.py
```

## What You'll See (for Screenshots)

The agent will display:
```
================================================================================
BROWSERBASE AGENT — FETCHING LATEST WATER MAIN BREAKS
================================================================================
Target: Kitchener Water Main Breaks FeatureServer
Time: 2026-06-21 XX:XX:XX
Using: Browserbase cloud browser platform
Project ID: proj_...
================================================================================

[1/5] Initializing Browserbase client...
      ✓ Browserbase client initialized

[2/5] Creating remote browser session in Browserbase cloud...
      ✓ Browserbase session started
      Session ID: sess_...
      Connect URL: wss://connect.browserbase.com/...

[3/5] Connecting to Browserbase remote browser via Playwright...
      ✓ Connected to remote Chromium browser in Browserbase cloud
      ✓ Browser page ready

[4/5] Navigating to Kitchener Water Main Breaks API...
      URL: https://services1.arcgis.com/.../Water_Main_Breaks...
      ✓ Navigated to https://services1.arcgis.com/.../Water_Main_Breaks
      HTTP Status: 200

[5/5] Extracting water main break data from API response...
      ✓ JSON response parsed successfully
      ✓ Pulled 20 water main break records from Kitchener

================================================================================
DATA SAMPLE — First Water Main Break Record:
================================================================================
  OBJECTID: 1234
  Street: King St
  Break Type: Main Break
  Status: Resolved
  Material: Cast Iron
  Source: Browserbase session sess_abc1...
================================================================================
```

## Output Files

After successful run:
- `latest_breaks.json` — 20 most recent water main break records
- `ingestion.log` — Timestamped log of all operations

## For Judges: What This Demonstrates

✓ **Browserbase Integration**: Creates cloud browser session via Browserbase API
✓ **Remote Browser Control**: Uses Playwright to control Browserbase's remote Chromium
✓ **Real Data**: Fetches genuine water infrastructure data from City of Kitchener
✓ **Visible Logging**: Clear 5-step process with checkmarks and session IDs
✓ **Production Use**: Actual integration (not a mock), outputs usable JSON data

## Troubleshooting

**"ERROR: Browserbase API key not configured"**
- Make sure you added your actual API key to config.json (starts with `bb_live_`)

**"playwright: command not found"**
- Run: `pip install playwright && playwright install chromium`

**"Connection timeout"**
- Check your internet connection
- Verify Browserbase account has available credits
- Try running again (first connection can be slow)

**"No features in API response"**
- The Kitchener API endpoint might be temporarily down
- Check if you can access it directly: https://services1.arcgis.com/qAo1OsXi67t7XgmS/ArcGIS/rest/services/Water_Main_Breaks/FeatureServer/0/query?where=1=1&f=json

## Screenshot Recommendations for Judges

1. **Terminal output** showing the 5 steps with checkmarks
2. **Session ID** visible in output (proves real Browserbase session)
3. **Data sample** showing actual Kitchener water main break records
4. **Output file** `latest_breaks.json` with real data
5. **Browserbase dashboard** (optional) showing active/completed sessions

---

Built for UC Berkeley AI Hackathon 2026 — Anthropic Prize Track
