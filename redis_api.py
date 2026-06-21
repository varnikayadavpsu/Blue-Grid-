#!/usr/bin/env python3
"""
Blue Grid — Redis Vector Search API

Provides API endpoint for finding similar water main breaks
using Redis vector search.

Run: python3 redis_api.py
Port: 5001
"""
import json
import sys
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    import redis
    from redis.commands.search.query import Query
except ImportError as e:
    print(f"ERROR: Missing or incompatible dependencies: {e}")
    print("\nInstall with:")
    print("  pip install 'redis>=5.0.0' flask flask-cors")
    print("\nNote: Requires redis-py 5.0+ with search capabilities")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

INDEX_NAME = "breaks_idx"

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    redis_url = config.get('redis_url')
except Exception as e:
    print(f"ERROR: Failed to load config.json: {e}")
    sys.exit(1)

# Connect to Redis
try:
    r = redis.from_url(redis_url, decode_responses=True)
    r.ping()
    print("\n" + "="*70)
    print("REDIS VECTOR SEARCH API")
    print("="*70)
    print("Status: Running")
    print("Port: 5001")
    print(f"Redis: Connected")
    print(f"Index: {INDEX_NAME}")
    print("Endpoint: http://localhost:5001/api/similar-breaks")
    print("="*70 + "\n")
except Exception as e:
    print(f"ERROR: Redis connection failed: {e}")
    sys.exit(1)

def create_query_vector(pipe_attrs):
    """
    Create vector from pipe attributes for similarity search.
    Same encoding as load_breaks_to_redis.py
    """
    material = str(pipe_attrs.get('material', '')).upper()
    material_map = {
        'CAST IRON': 1.0,
        'DUCTILE IRON': 0.8,
        'PVC': 0.3,
        'STEEL': 0.9,
        'CONCRETE': 0.6,
        'HDPE': 0.2,
    }
    material_code = material_map.get(material, 0.5)

    age = float(pipe_attrs.get('age', 50))
    diameter = float(pipe_attrs.get('diameter', 150))
    lat = float(pipe_attrs.get('lat', 43.45))
    lon = float(pipe_attrs.get('lon', -80.49))

    vector = np.array([
        material_code,
        age / 100.0,
        diameter / 500.0,
        (lat - 43.4) * 100,
        (lon + 80.5) * 100
    ], dtype=np.float32)

    return vector

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        r.ping()
        return jsonify({
            'status': 'ok',
            'service': 'redis-vector-search',
            'redis': 'connected'
        })
    except:
        return jsonify({
            'status': 'error',
            'service': 'redis-vector-search',
            'redis': 'disconnected'
        }), 500

@app.route('/api/similar-breaks', methods=['POST'])
def find_similar_breaks():
    """
    Find similar past water main breaks using vector search.

    Request body:
    {
        "material": "Cast Iron",
        "age": 60,
        "diameter": 200,
        "lat": 43.45,
        "lon": -80.49,
        "top_k": 3
    }

    Response:
    {
        "success": true,
        "query": {...},
        "similar_breaks": [
            {
                "street": "King St",
                "material": "Cast Iron",
                "break_type": "Main Break",
                "similarity": 0.95
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Extract pipe attributes
        material = data.get('material', 'Unknown')
        age = data.get('age', 50)
        diameter = data.get('diameter', 150)
        lat = data.get('lat', 43.45)
        lon = data.get('lon', -80.49)
        top_k = data.get('top_k', 3)

        print(f"Searching for breaks similar to: {material}, {age}yr, {diameter}mm")

        # Create query vector
        query_vector = create_query_vector({
            'material': material,
            'age': age,
            'diameter': diameter,
            'lat': lat,
            'lon': lon
        })

        # Execute vector search
        query = (
            Query(f"*=>[KNN {top_k} @vector $vec AS score]")
            .return_fields("street", "material", "break_type", "status", "score")
            .sort_by("score")
            .dialect(2)
        )

        results = r.ft(INDEX_NAME).search(
            query,
            query_params={"vec": query_vector.tobytes()}
        )

        # Format results
        similar_breaks = []
        for doc in results.docs:
            similar_breaks.append({
                'street': doc.street,
                'material': doc.material,
                'break_type': doc.break_type,
                'status': getattr(doc, 'status', 'Unknown'),
                'similarity': float(doc.score)
            })

        print(f"✓ Found {len(similar_breaks)} similar breaks")

        return jsonify({
            'success': True,
            'query': {
                'material': material,
                'age': age,
                'diameter': diameter,
                'location': f"{lat:.4f}, {lon:.4f}"
            },
            'similar_breaks': similar_breaks,
            'count': len(similar_breaks)
        })

    except redis.ResponseError as e:
        error_msg = str(e)
        if 'no such index' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'Redis index not found. Run: python3 load_breaks_to_redis.py'
            }), 500
        return jsonify({'success': False, 'error': f'Redis error: {error_msg}'}), 500

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Run on port 5001 (anthropic_proxy uses 5002)
    app.run(host='0.0.0.0', port=5001, debug=False)
