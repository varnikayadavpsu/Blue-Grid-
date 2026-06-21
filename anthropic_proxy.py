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
print("Endpoints:")
print("  - http://localhost:5002/api/action-plan")
print("  - http://localhost:5002/api/explain-pipe")
print("Model: claude-haiku-4-5-20251001 (low cost)")
print("API Key: Loaded from config.json ✓")
print("="*70 + "\n")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'anthropic-proxy',
        'model': 'claude-haiku-4-5-20251001'
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
        prompt = f"""Water ops engineer reviewing zone {zone_name} (Risk {risk}/100, {breaks} historical breaks).

Write a quick 72-hour action plan. Three sections, 2-3 short bullets each. Plain language like you're briefing the crew lead:

IMMEDIATE (0-24h):
- [what to inspect/monitor now]

72-HOUR (24-72h):
- [follow-up work]

LONG-TERM (1-6mo):
- [planning/upgrades]

No preamble. Direct, scannable bullets only."""

        # Call Claude API (using Haiku for low cost)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
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
            'model': 'claude-haiku-4-5-20251001'
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

@app.route('/api/explain-pipe', methods=['POST'])
def explain_pipe():
    """Explain why a pipe/zone is at risk using Claude"""
    try:
        # Get pipe/zone data from request
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract data (works for both pipes and zones)
        pipe_id = data.get('pipe_id') or data.get('zone_id', 'Unknown')
        neighborhood = data.get('neighborhood', '')
        risk = data.get('risk', 0)
        age = data.get('age', 0)
        material = data.get('material', 'Unknown')
        diameter = data.get('diameter', 'Unknown')
        age_factor = data.get('age_factor', 0)
        material_fragility = data.get('material_fragility', 0)
        break_history = data.get('break_history', 0)
        flood_factor = data.get('flood_factor', 0)
        breaks = data.get('breaks', 0)
        segments = data.get('segments', 0)

        print(f"Explaining risk for: {pipe_id} (Risk: {risk})")

        # Build prompt - focus on WHY this pipe is at risk
        if neighborhood:
            # Zone explanation
            prompt = f"""Zone {neighborhood}: risk {risk}/100. Top factors: age={age_factor}, material={material_fragility}, history={break_history}, {breaks} past breaks.

Write 2-3 short sentences explaining why this zone is at risk. Sound like a city engineer writing notes, not an AI. Focus on the main risk drivers. No fluff."""
        else:
            # Pipe explanation
            prompt = f"""Pipe {pipe_id}: {age}yr {material}, risk {risk}/100. Main factors: age={age_factor}, material={material_fragility}, history={break_history}.

Write 2-3 short sentences explaining why this pipe is at risk. Sound like a city engineer writing notes, not an AI. Focus on the top risk factor and the material/age combo. No fluff."""

        # Call Claude API (using Haiku for low cost)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract response text
        response_text = message.content[0].text

        print(f"✓ Explanation generated ({len(response_text)} chars)")

        return jsonify({
            'success': True,
            'explanation': response_text,
            'pipe_id': pipe_id,
            'model': 'claude-haiku-4-5-20251001'
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
