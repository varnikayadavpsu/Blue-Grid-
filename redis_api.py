#!/usr/bin/env python3
"""
Blue Grid — Redis Vector Similarity API

Simple Flask API to query similar break records from Redis.

Dependencies: pip install flask flask-cors redis sentence-transformers
Run: python redis_api.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
import numpy as np
import json

app = Flask(__name__)
CORS(app)  # Allow requests from the dashboard

# Redis connection
REDIS_HOST = "localhost"
REDIS_PORT = 6379
INDEX_NAME = "break_similarity_idx"
VECTOR_DIM = 384

# Load model once at startup
print("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

# Connect to Redis
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
    redis_client.ping()
    print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError:
    print(f"ERROR: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
    print("Make sure Redis is running and setup_redis.py has been executed.")
    exit(1)

def create_zone_embedding(zone_data):
    """Create embedding for a zone's profile"""
    material_names = {
        100: "cast iron (high fragility)",
        50: "ductile iron (medium fragility)",
        20: "PVC (low fragility)",
        15: "HDPE (low fragility)"
    }

    material = zone_data.get('material', 50)
    material_desc = material_names.get(material, f"material fragility {material}")

    age = zone_data.get('age', 60)
    age_desc = f"{age} years old" if age > 0 else "age unknown"

    breaks = zone_data.get('breaks', 0)
    break_desc = f"{breaks} historical breaks" if breaks > 0 else "no recorded breaks"

    segments = zone_data.get('segments', 0)
    break_history = zone_data.get('break_history', 0)

    description = (
        f"Water infrastructure zone with {material_desc}, "
        f"{age_desc}, {break_desc}, "
        f"break history factor {break_history}, "
        f"serving {segments} pipe segments"
    )

    embedding = model.encode(description, normalize_embeddings=True)
    return embedding.astype(np.float32).tobytes()

@app.route('/api/similar-breaks', methods=['POST'])
def find_similar_breaks():
    """Find similar break records for a given zone"""
    try:
        data = request.json

        # Extract zone profile
        zone_profile = {
            'age': data.get('age', 60),
            'material': data.get('material', 50),
            'breaks': data.get('breaks', 0),
            'segments': data.get('segments', 1),
            'break_history': data.get('break_history', 0)
        }

        # Create embedding
        embedding = create_zone_embedding(zone_profile)

        # Query Redis for similar vectors
        k = data.get('top_k', 5)
        query = (
            Query(f"*=>[KNN {k} @embedding $vec AS score]")
            .return_fields("zone_id", "description", "risk_score", "breaks", "age", "material", "lat", "lon", "score")
            .sort_by("score")
            .dialect(2)
        )

        result = redis_client.ft(INDEX_NAME).search(
            query,
            query_params={"vec": embedding}
        )

        # Format results
        similar_breaks = []
        for doc in result.docs:
            similar_breaks.append({
                'zone_id': doc.zone_id.decode('utf-8') if isinstance(doc.zone_id, bytes) else doc.zone_id,
                'description': doc.description.decode('utf-8') if isinstance(doc.description, bytes) else doc.description,
                'risk_score': int(doc.risk_score.decode('utf-8') if isinstance(doc.risk_score, bytes) else doc.risk_score),
                'breaks': int(doc.breaks.decode('utf-8') if isinstance(doc.breaks, bytes) else doc.breaks),
                'age': int(doc.age.decode('utf-8') if isinstance(doc.age, bytes) else doc.age),
                'material': int(doc.material.decode('utf-8') if isinstance(doc.material, bytes) else doc.material),
                'similarity': round(1 - float(doc.score), 3)  # Convert distance to similarity
            })

        return jsonify({
            'success': True,
            'similar_breaks': similar_breaks
        })

    except Exception as e:
        print(f"Error in similarity search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'redis_connected': True,
            'index_name': INDEX_NAME
        })
    except:
        return jsonify({
            'status': 'unhealthy',
            'redis_connected': False
        }), 503

if __name__ == '__main__':
    print("\n" + "="*60)
    print("BLUE GRID — REDIS VECTOR SIMILARITY API")
    print("="*60)
    print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Index: {INDEX_NAME}")
    print(f"Vector dimension: {VECTOR_DIM}")
    print("="*60)
    print("\nStarting Flask server on http://localhost:5001")
    print("Endpoints:")
    print("  POST /api/similar-breaks - Find similar break records")
    print("  GET  /api/health         - Health check")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5001, debug=False)
