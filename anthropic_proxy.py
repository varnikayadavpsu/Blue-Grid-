#!/usr/bin/env python3
"""
Blue Grid - Anthropic API Proxy Server

This proxy server:
- Reads the Anthropic API key from config.json (server-side)
- Exposes /api/action-plan endpoint for the dashboard
- Forwards requests to Anthropic API
- Handles CORS to allow browser requests
- Keeps API key secure (never exposed to browser)

Run: python anthropic_proxy.py
Port: 5002
"""

import json
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Check dependencies
try:
    import anthropic
except ImportError:
    print("ERROR: Missing anthropic package. Install with:")
    print("  pip install anthropic flask flask-cors")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load API key from config.json
def load_config():
    """Load Anthropic API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        api_key = config.get('anthropicApiKey')
        if not api_key or api_key == 'YOUR_ANTHROPIC_API_KEY_HERE':
            print("\n" + "="*70)
            print("ERROR: Anthropic API key not configured")
            print("="*70)
            print("Please add your API key to config.json:")
            print("  1. Get key from: https://console.anthropic.com/")
            print("  2. Edit config.json and replace YOUR_ANTHROPIC_API_KEY_HERE")
            print("  3. Restart this server")
            print("="*70 + "\n")
            sys.exit(1)

        return api_key
    except FileNotFoundError:
        print("ERROR: config.json not found")
        sys.exit(1)

# Initialize Anthropic client
API_KEY = load_config()
client = anthropic.Anthropic(api_key=API_KEY)

print("\n" + "="*70)
print("ANTHROPIC API PROXY SERVER")
print("="*70)
print("Status: Running")
print("Port: 5002")
print("Endpoint: http://localhost:5002/api/action-plan")
print("Model: claude-3-haiku-20240307 (low cost)")
print("API Key: Loaded from config.json ✓")
print("="*70 + "\n")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'anthropic-proxy',
        'model': 'claude-3-haiku-20240307'
    })

@app.route('/api/action-plan', methods=['POST'])
def generate_action_plan():
    """Generate action plan for a zone using Claude"""
    try:
        # Get zone data from request
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        zone_name = data.get('name', 'Unknown Zone')
        zone_id = data.get('id', '')
        risk = data.get('risk', 0)
        age = data.get('age', 0)
        material = data.get('material', 0)
        break_history = data.get('break_history', 0)
        breaks = data.get('breaks', 0)
        segments = data.get('segments', 0)

        print(f"Generating action plan for: {zone_name} (Risk: {risk})")

        # Build prompt
        prompt = f"""You are a municipal water infrastructure operations expert. Generate a concise, actionable 72-hour operational plan for this high-risk water infrastructure zone:

Zone: {zone_name} ({zone_id})
Risk Score: {risk}/100
Infrastructure Age Factor: {age}
Material Fragility Factor: {material}
Break History Factor: {break_history}
Historical Breaks: {breaks}
Pipe Segments: {segments}

Generate a structured action plan with exactly THREE sections:

**IMMEDIATE ACTIONS (0-24 hours)**
- [3-4 specific urgent actions with bullet points]

**72-HOUR ACTIONS (24-72 hours)**
- [3-4 specific medium-term actions with bullet points]

**LONG-TERM ACTIONS (1-6 months)**
- [3-4 specific strategic actions with bullet points]

Be specific, operational, and concise. Each action should be clear and actionable for city crews."""

        # Call Claude API (using Haiku for low cost)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract response text
        response_text = message.content[0].text

        print(f"✓ Plan generated ({len(response_text)} chars)")

        return jsonify({
            'success': True,
            'plan': response_text,
            'zone': zone_name,
            'model': 'claude-3-haiku-20240307'
        })

    except anthropic.APIError as e:
        print(f"✗ Anthropic API error: {e}")
        return jsonify({
            'success': False,
            'error': f'API error: {str(e)}'
        }), 500

    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='localhost', port=5002, debug=False)
