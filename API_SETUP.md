# Blue Grid — Action Plan API Setup

## Quick Start

To enable the AI-powered "Generate Action Plan" feature:

1. **Get your Anthropic API key:**
   - Visit https://console.anthropic.com/
   - Sign in or create an account
   - Navigate to API Keys
   - Create a new API key

2. **Add the key to config.json:**
   ```bash
   cd ~/Desktop/bluegrid
   # Edit config.json and replace YOUR_ANTHROPIC_API_KEY_HERE with your actual key
   ```

   The file should look like:
   ```json
   {
     "anthropicApiKey": "sk-ant-xxxxxxxxxxxxxxxxxxxxx"
   }
   ```

3. **Start the server (if not already running):**
   ```bash
   python3 -m http.server 8000
   ```

4. **Test it:**
   - Open http://localhost:8000/landing.html
   - Click "Enter Command Center"
   - Click any high-risk zone or priority item
   - Click "Generate Action Plan"
   - Watch Claude generate a real 72-hour operational plan!

## Security Note

**IMPORTANT:** `config.json` is in `.gitignore` and will NOT be committed to git. Never commit your API key to version control.

## How It Works

When you click "Generate Action Plan":
1. The dashboard sends the zone's real data to Claude (neighborhood, risk score, factors, break history)
2. Claude analyzes the data and generates a structured 72-hour operational plan with:
   - **Immediate Actions** (0-24 hours) - urgent inspections, crew deployment
   - **72-Hour Actions** (24-72 hours) - detailed assessments, preventive measures
   - **Long-Term Actions** (1-6 months) - infrastructure upgrades, monitoring
3. The plan is rendered in a clean, readable format in the detail panel

## Error Handling

- **No API key configured:** Shows a friendly error message asking you to add the key
- **API request fails:** Displays the error without crashing the dashboard
- **Network issues:** Gracefully handles connection problems

## Demo Without API Key

The dashboard works fully without an API key — you just won't be able to generate action plans. All other features (map, risk visualization, zone details, factor breakdowns) work perfectly.
