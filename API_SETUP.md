# Blue Grid — API Setup Guide

## Anthropic Claude API (Action Plan Feature)

### 1. Get Your API Key

1. Visit https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy your API key (starts with `sk-ant-`)

### 2. Add Key to config.json

**IMPORTANT:** Your API key goes in `config.json` which is **gitignored** and never committed.

```bash
cd ~/Desktop/bluegrid
```

Edit `config.json` and replace the placeholder:

```json
{
  "anthropicApiKey": "sk-ant-api03-YOUR-ACTUAL-KEY-HERE",
  "browserbaseApiKey": "YOUR_BROWSERBASE_API_KEY_HERE"
}
```

**Example:**
```json
{
  "anthropicApiKey": "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "browserbaseApiKey": "YOUR_BROWSERBASE_API_KEY_HERE"
}
```

✓ Confirm `config.json` is in `.gitignore` (it is!)

### 3. Install Python Dependencies

```bash
pip install anthropic flask flask-cors
```

### 4. Start the Proxy Server

The proxy server keeps your API key secure by reading it server-side and forwarding requests to Anthropic.

**Open a NEW terminal window** and run:

```bash
cd ~/Desktop/bluegrid
python anthropic_proxy.py
```

You should see:
```
======================================================================
ANTHROPIC API PROXY SERVER
======================================================================
Status: Running
Port: 5002
Endpoint: http://localhost:5002/api/action-plan
Model: claude-3-haiku-20240307 (low cost)
API Key: Loaded from config.json ✓
======================================================================
```

**Keep this terminal open!** The proxy must stay running.

### 5. Start the Dashboard Server

**In a SECOND terminal window:**

```bash
cd ~/Desktop/bluegrid
python3 -m http.server 8000
```

### 6. Test the Action Plan Feature

1. Open http://localhost:8000/landing.html
2. Click **"Enter Command Center"**
3. Click any **red zone** on the map (high-risk zones)
4. In the detail panel, click **"Generate Action Plan"**
5. Watch the loading state: "Analyzing zone data with Claude Haiku..."
6. After ~3-5 seconds, you'll see a real AI-generated plan with:
   - **IMMEDIATE ACTIONS** (0-24 hours)
   - **72-HOUR ACTIONS** (24-72 hours)
   - **LONG-TERM ACTIONS** (1-6 months)

### Quick Test Checklist

```
□ config.json has real API key (sk-ant-...)
□ anthropic_proxy.py is running (terminal 1)
□ python3 -m http.server 8000 is running (terminal 2)
□ Open http://localhost:8000/landing.html
□ Click high-risk zone (red marker)
□ Click "Generate Action Plan"
□ Plan appears in ~3-5 seconds
```

### 7. Troubleshooting

**Error: "Cannot connect to API proxy server"**
- Make sure `anthropic_proxy.py` is running in a separate terminal
- Check that you're on port 5002 (not in use by another app)
- Try: `curl http://localhost:5002/health` (should return `{"status":"ok"}`)

**Error: "API key not configured"**
- Edit config.json and replace `YOUR_ANTHROPIC_API_KEY_HERE`
- Restart `anthropic_proxy.py` after editing config.json
- Your key should start with `sk-ant-`

**Proxy won't start:**
```bash
# Install missing dependencies
pip install anthropic flask flask-cors

# Check Python version (needs 3.7+)
python --version
```

**Plan doesn't appear:**
- Open browser console (F12) and check for errors
- Make sure both servers are running (proxy + dashboard)
- Check ingestion.log for details

---

## Security Note

✓ **API key stored server-side** in `config.json` (gitignored)
✓ **Never exposed to browser** - proxy handles all Anthropic requests
✓ **CORS handled** by Flask proxy
✓ **No API key in front-end code**

`config.json` is in `.gitignore` and will **never** be committed to Git.

---

## How It Works

### Architecture

```
Browser (index.html)
    ↓ POST /api/action-plan
Local Proxy Server (anthropic_proxy.py:5002)
    ↓ reads API key from config.json
Anthropic API (api.anthropic.com)
    ↓ returns plan
Local Proxy Server
    ↓ JSON response
Browser (renders plan)
```

### Request Flow

1. User clicks "Generate Action Plan"
2. Dashboard sends zone data to `http://localhost:5002/api/action-plan`:
   ```json
   {
     "name": "Eastwood",
     "id": "43.45_-80.46",
     "risk": 95,
     "age": 60,
     "material": 100,
     "break_history": 25,
     "breaks": 10,
     "segments": 15
   }
   ```
3. Proxy reads API key from config.json (server-side)
4. Proxy calls Anthropic API with Claude Haiku (low cost)
5. Claude generates structured 72-hour plan
6. Proxy returns plan to browser
7. Dashboard renders plan with formatting

### Cost

**Model:** Claude 3 Haiku (cheapest, fast)
**Cost:** ~$0.0003 per plan (~1000 tokens)
**Budget:** $5 credit = ~16,000 plans

---

## Demo Without API Key

The dashboard works fully without the action plan feature:
- ✓ Map visualization
- ✓ Zone details
- ✓ Factor breakdowns
- ✓ Risk legend
- ✗ Generate Action Plan (requires API key)
