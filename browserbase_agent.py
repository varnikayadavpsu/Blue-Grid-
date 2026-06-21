#!/usr/bin/env python3
"""
Blue Grid — Browserbase Data Ingestion Agent

Uses Browserbase cloud browser to fetch the latest water main break records from
City of Kitchener's ArcGIS REST API.

This demonstrates Browserbase integration by:
  - Creating a remote browser session in Browserbase's cloud
  - Using Playwright to control the browser
  - Fetching data from Kitchener's public FeatureServer
  - Outputting in a format compatible with build_data.py

Dependencies: pip install browserbase playwright
Setup:
  1. Sign up at https://www.browserbase.com/ (use code: STARTERPACK)
  2. Get your API key from the dashboard
  3. Add to config.json:
     {
       "browserbaseApiKey": "bb_..."
     }
  4. Install Playwright browsers: playwright install chromium

Run: python browserbase_agent.py
Output: latest_breaks.json (compatible with build_data.py)
"""

import json
import sys
from datetime import datetime

try:
    from browserbase import Browserbase
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Missing dependencies. Install with:")
    print("  pip install browserbase playwright")
    print("  playwright install chromium")
    sys.exit(1)

# Configuration - Kitchener Water Main Breaks FeatureServer
BREAKS_API_URL = "https://services1.arcgis.com/qAo1OsXi67t7XgmS/ArcGIS/rest/services/Water_Main_Breaks/FeatureServer/0/query"
OUTPUT_FILE = "latest_breaks.json"
LOG_FILE = "ingestion.log"

def load_config():
    """Load API keys from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        bb_key = config.get('browserbaseApiKey')
        if not bb_key or bb_key == 'YOUR_BROWSERBASE_API_KEY_HERE':
            print("ERROR: Browserbase API key not configured in config.json")
            print("Get your key from https://www.browserbase.com/")
            sys.exit(1)

        return config
    except FileNotFoundError:
        print("ERROR: config.json not found")
        sys.exit(1)

def log_to_file(message):
    """Append message to log file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def fetch_latest_breaks(api_key):
    """Use Browserbase to fetch latest break records from Kitchener ArcGIS REST API"""
    print("\n" + "="*80)
    print("BROWSERBASE AGENT — FETCHING LATEST WATER MAIN BREAKS")
    print("="*80)
    print(f"Target: Kitchener Water Main Breaks FeatureServer")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using: Browserbase cloud browser platform")
    print("="*80 + "\n")

    log_to_file("Starting Browserbase agent")

    try:
        # Initialize Browserbase client
        print("Initializing Browserbase client...")
        bb = Browserbase(api_key=api_key)
        log_to_file("Browserbase client initialized")

        # Create a session in Browserbase's cloud
        print("Creating remote browser session in Browserbase cloud...")
        session = bb.sessions.create(project_id=None)  # Uses default project
        session_id = session.id
        connect_url = session.connect_url

        print(f"✓ Session created: {session_id}")
        print(f"  Connect URL: {connect_url[:50]}...")
        log_to_file(f"Session created: {session_id}")

        # Connect to the remote browser using Playwright
        print("\nConnecting to Browserbase remote browser via Playwright...")
        with sync_playwright() as playwright:
            # Connect to the Browserbase browser over Chrome DevTools Protocol
            browser = playwright.chromium.connect_over_cdp(connect_url)
            print(f"✓ Connected to remote Chromium browser")
            log_to_file("Connected to Browserbase browser")

            # Get the default context and page
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()

            print(f"✓ Browser page ready")

            # Build the ArcGIS REST API query URL to get recent breaks
            # Query params: where=1=1 (all records), outFields=*, f=json, orderByFields=OBJECTID DESC, resultRecordCount=20
            query_url = (
                f"{BREAKS_API_URL}?"
                f"where=1=1&"
                f"outFields=*&"
                f"orderByFields=OBJECTID+DESC&"
                f"resultRecordCount=20&"
                f"f=json"
            )

            print(f"\nNavigating to ArcGIS REST API endpoint...")
            print(f"  URL: {query_url[:80]}...")

            # Navigate to the API endpoint
            response = page.goto(query_url, wait_until='networkidle', timeout=30000)
            print(f"✓ Page loaded (HTTP {response.status})")
            log_to_file(f"Navigated to API endpoint: HTTP {response.status}")

            # Extract the JSON response from the page
            print("\nExtracting JSON data from response...")
            page_content = page.content()

            # The page will display raw JSON - extract it
            json_text = page.evaluate('document.body.innerText')

            # Parse the JSON response
            try:
                data = json.loads(json_text)
                print(f"✓ JSON parsed successfully")

                if 'features' in data:
                    features = data['features']
                    print(f"✓ Found {len(features)} break records")
                    log_to_file(f"Extracted {len(features)} break records")

                    # Convert to simplified format
                    breaks = []
                    for feature in features:
                        attrs = feature.get('attributes', {})
                        geom = feature.get('geometry', {})

                        breaks.append({
                            'OBJECTID': attrs.get('OBJECTID'),
                            'INCIDENT_DATE': attrs.get('INCIDENT_DATE') or attrs.get('DATE'),
                            'STREET': attrs.get('STREET') or attrs.get('LOCATION'),
                            'BREAK_TYPE': attrs.get('BREAK_TYPE') or attrs.get('TYPE'),
                            'STATUS': attrs.get('STATUS'),
                            'ASSET_MATERIAL': attrs.get('ASSET_MATERIAL') or attrs.get('MATERIAL'),
                            'ASSET_SIZE': attrs.get('ASSET_SIZE') or attrs.get('DIAMETER'),
                            'geometry': geom,
                            '_scraped_at': datetime.now().isoformat(),
                            '_source': 'browserbase_agent',
                            '_session_id': session_id
                        })

                    print(f"\nSample record (first break):")
                    if breaks:
                        print(f"  OBJECTID: {breaks[0].get('OBJECTID')}")
                        print(f"  Street: {breaks[0].get('STREET')}")
                        print(f"  Type: {breaks[0].get('BREAK_TYPE')}")
                        print(f"  Status: {breaks[0].get('STATUS')}")

                    # Close browser
                    print("\nClosing browser session...")
                    browser.close()
                    log_to_file("Browser session closed")

                    return breaks
                else:
                    print("✗ No 'features' field in response")
                    log_to_file("ERROR: No features in API response")
                    browser.close()
                    return []

            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse JSON: {e}")
                print(f"  Page content preview: {json_text[:200]}...")
                log_to_file(f"JSON parse error: {e}")
                browser.close()
                return []

    except Exception as e:
        print(f"\n✗ Error during Browserbase session: {e}")
        print(f"  Error type: {type(e).__name__}")
        log_to_file(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_breaks(breaks, filename):
    """Save breaks to JSON file"""
    output = {
        "city": "Kitchener, ON",
        "source": "Browserbase Agent",
        "scraped_at": datetime.now().isoformat(),
        "count": len(breaks),
        "breaks": breaks
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved {len(breaks)} break records to {filename}")

def main():
    print("\n" + "="*80)
    print("BLUE GRID — BROWSERBASE DATA INGESTION AGENT")
    print("="*80)

    # Load configuration
    config = load_config()

    # Fetch latest breaks using Browserbase
    breaks = fetch_latest_breaks(config.get('browserbaseApiKey'))

    # Save to file
    if breaks and len(breaks) > 0:
        save_breaks(breaks, OUTPUT_FILE)

        print("\n" + "="*80)
        print("✓ AGENT COMPLETE — DATA SUCCESSFULLY FETCHED VIA BROWSERBASE")
        print("="*80)
        print(f"Output file: {OUTPUT_FILE}")
        print(f"Records fetched: {len(breaks)}")
        print(f"Log file: {LOG_FILE}")
        print("\nWhat was demonstrated:")
        print("  ✓ Browserbase session created in cloud")
        print("  ✓ Remote browser controlled via Playwright")
        print("  ✓ Data fetched from Kitchener ArcGIS REST API")
        print("  ✓ Records extracted and saved to JSON")
        print("\nNext steps:")
        print("  1. Review latest_breaks.json")
        print("  2. Integrate with build_data.py pipeline if needed")
        print("  3. Schedule daily/weekly runs for continuous updates")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("✗ AGENT FAILED — NO DATA FETCHED")
        print("="*80)
        print("Troubleshooting:")
        print("  1. Check your Browserbase API key in config.json")
        print("  2. Ensure you have Browserbase credits (sign up with STARTERPACK)")
        print("  3. Check ingestion.log for details")
        print("  4. Verify Playwright is installed: playwright install chromium")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
