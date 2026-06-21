#!/usr/bin/env python3
"""
Blue Grid — Browserbase Data Ingestion Agent

Uses Browserbase cloud browser to fetch real water main break data from
City of Kitchener's open data portal (ArcGIS REST API).

Run: python3 browserbase_agent.py
"""
import json
import sys
from datetime import datetime

try:
    from browserbase import Browserbase
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Missing dependencies. Run:")
    print("  pip install browserbase playwright")
    print("  playwright install chromium")
    sys.exit(1)

# City of Kitchener Water Main Breaks API endpoint
KITCHENER_API = "https://services1.arcgis.com/qAo1OsXi67t7XgmS/ArcGIS/rest/services/Water_Main_Breaks/FeatureServer/0/query"

def main():
    print("\n" + "="*80)
    print("BLUE GRID — BROWSERBASE DATA INGESTION AGENT")
    print("="*80)
    print("Target: City of Kitchener Water Main Breaks (Open Data)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('browserbaseApiKey')
        project_id = config.get('browserbaseProjectId')
        print(f"\n✓ Loaded credentials from config.json")
    except Exception as e:
        print(f"\n✗ Failed to load config.json: {e}")
        sys.exit(1)

    try:
        # Step 1: Initialize Browserbase
        print("\n[1/5] Initializing Browserbase client...")
        bb = Browserbase(api_key=api_key)
        print("      ✓ Browserbase client initialized")

        # Step 2: Create session
        print("\n[2/5] Creating Browserbase session...")
        session = bb.sessions.create(project_id=project_id)
        session_id = session.id
        connect_url = session.connect_url
        print(f"      ✓ Browserbase session started")
        print(f"      Session ID: {session_id}")

        # Step 3: Connect to remote browser
        print("\n[3/5] Connecting to Browserbase remote browser...")
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(connect_url)
            print("      ✓ Connected to Browserbase cloud browser")

            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()

            # Step 4: Navigate to Kitchener API
            print("\n[4/5] Navigating to City of Kitchener Water Main Breaks API...")

            # Build query URL: get recent records, all fields, JSON format
            query_url = (
                f"{KITCHENER_API}?"
                f"where=1=1&"
                f"outFields=*&"
                f"orderByFields=OBJECTID+DESC&"
                f"resultRecordCount=10&"
                f"f=json"
            )

            print(f"      URL: {KITCHENER_API}")
            page.goto(query_url, wait_until='networkidle', timeout=30000)
            print(f"      ✓ Navigated to Kitchener Open Data API")

            # Step 5: Extract data
            print("\n[5/5] Extracting water main break records...")

            # Get the JSON response from the page
            json_text = page.evaluate('document.body.innerText')
            data = json.loads(json_text)

            if 'features' in data:
                features = data['features']
                record_count = len(features)
                print(f"      ✓ Pulled {record_count} water main break records from Kitchener")

                # Display records
                print("\n" + "="*80)
                print("WATER MAIN BREAK RECORDS — CITY OF KITCHENER")
                print("="*80)

                for i, feature in enumerate(features[:5], 1):  # Show first 5
                    attrs = feature.get('attributes', {})
                    print(f"\nRecord #{i}:")
                    print(f"  OBJECTID:       {attrs.get('OBJECTID', 'N/A')}")
                    print(f"  Date:           {attrs.get('INCIDENT_DATE', attrs.get('DATE', 'N/A'))}")
                    print(f"  Location:       {attrs.get('STREET', attrs.get('LOCATION', 'N/A'))}")
                    print(f"  Break Type:     {attrs.get('BREAK_TYPE', attrs.get('TYPE', 'N/A'))}")
                    print(f"  Status:         {attrs.get('STATUS', 'N/A')}")
                    print(f"  Material:       {attrs.get('ASSET_MATERIAL', attrs.get('MATERIAL', 'N/A'))}")
                    print(f"  Diameter:       {attrs.get('ASSET_SIZE', attrs.get('DIAMETER', 'N/A'))}")

                if record_count > 5:
                    print(f"\n... and {record_count - 5} more records")

                print("="*80)

                # Save to file
                output = {
                    "source": "Browserbase Agent - City of Kitchener Open Data",
                    "scraped_at": datetime.now().isoformat(),
                    "browserbase_session_id": session_id,
                    "count": record_count,
                    "records": [f.get('attributes', {}) for f in features]
                }

                with open('latest_breaks.json', 'w') as f:
                    json.dump(output, f, indent=2)

                print(f"\n✓ Saved {record_count} records to latest_breaks.json")

            else:
                print("      ✗ No features found in API response")
                record_count = 0

            # Close browser
            print("\nClosing Browserbase session...")
            browser.close()
            print("      ✓ Session closed")

        # Success summary
        print("\n" + "="*80)
        print("✓ BROWSERBASE AGENT COMPLETE")
        print("="*80)
        print(f"Records fetched: {record_count}")
        print(f"Output file: latest_breaks.json")
        print(f"Session ID: {session_id}")
        print("\nWhat was demonstrated:")
        print("  ✓ Browserbase session created in cloud")
        print("  ✓ Remote browser controlled via Playwright")
        print("  ✓ Real data fetched from City of Kitchener Open Data")
        print("  ✓ Records extracted and saved to JSON")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("  - Verify API credentials in config.json")
        print("  - Check Browserbase account has credits")
        print("  - Ensure Playwright is installed: playwright install chromium")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
