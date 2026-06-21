#!/usr/bin/env python3
"""
Minimal Browserbase connectivity test
"""
import json
import sys

try:
    from browserbase import Browserbase
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Missing dependencies. Run:")
    print("  pip install browserbase playwright")
    sys.exit(1)

print("\n" + "="*60)
print("BROWSERBASE CONNECTIVITY TEST")
print("="*60)

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    api_key = config.get('browserbaseApiKey')
    project_id = config.get('browserbaseProjectId')
    print(f"✓ Loaded config.json")
    print(f"  API Key: {api_key[:20]}...")
    print(f"  Project ID: {project_id}")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    sys.exit(1)

try:
    # Initialize Browserbase
    print("\n[1/4] Initializing Browserbase client...")
    bb = Browserbase(api_key=api_key)
    print("      ✓ Browserbase client initialized")

    # Create session
    print("\n[2/4] Creating Browserbase session...")
    session = bb.sessions.create(project_id=project_id)
    session_id = session.id
    connect_url = session.connect_url
    print(f"      ✓ Session created: {session_id}")
    print(f"      Connect URL: {connect_url[:50]}...")

    # Connect with Playwright
    print("\n[3/4] Connecting to remote browser...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(connect_url)
        print("      ✓ Connected to Browserbase")

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        # Navigate to example.com
        print("\n[4/4] Testing navigation to https://example.com...")
        page.goto("https://example.com", timeout=15000)
        title = page.title()
        print(f"      ✓ Page loaded successfully")
        print(f"      Page Title: '{title}'")

        browser.close()
        print("\n      ✓ Browser closed")

    print("\n" + "="*60)
    print("✓ BROWSERBASE CONNECTION TEST PASSED")
    print("="*60 + "\n")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")
    print("\nTroubleshooting:")
    print("  - Verify API key in config.json")
    print("  - Check Browserbase account has credits")
    print("  - Ensure internet connection is stable")
    print("="*60 + "\n")
    sys.exit(1)
