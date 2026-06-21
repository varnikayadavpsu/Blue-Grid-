#!/usr/bin/env python3
"""
Blue Grid — Redis Vector Search Setup

Embeds historical break records and creates a Redis vector index for similarity search.

Dependencies: pip install redis sentence-transformers numpy
Run: python setup_redis.py
"""

import json
import numpy as np
import redis
from redis.commands.search.field import VectorField, TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
import sys

# Redis connection
REDIS_HOST = "localhost"
REDIS_PORT = 6379
INDEX_NAME = "break_similarity_idx"
VECTOR_DIM = 384  # all-MiniLM-L6-v2 dimension

def connect_redis():
    """Connect to Redis"""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
        client.ping()
        print(f"✓ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return client
    except redis.ConnectionError:
        print(f"✗ Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
        print("  Make sure Redis is running: redis-server")
        sys.exit(1)

def load_zones_data():
    """Load zones.json to extract break records"""
    try:
        with open('zones.json', 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data['zones'])} zones from zones.json")
        return data['zones']
    except FileNotFoundError:
        print("✗ zones.json not found. Run build_data.py first.")
        sys.exit(1)

def create_break_embedding(zone, model):
    """Create a semantic embedding for a zone's break profile"""
    # Build a descriptive text representation of the zone's risk profile
    neighborhood = zone['id']  # Using coordinate ID as identifier

    # Material mapping for readability
    material_names = {
        100: "cast iron (high fragility)",
        50: "ductile iron (medium fragility)",
        20: "PVC (low fragility)",
        15: "HDPE (low fragility)"
    }
    material = zone['factors']['material']
    material_desc = material_names.get(material, f"material fragility {material}")

    # Age description
    age = zone['factors']['age']
    age_desc = f"{age} years old" if age > 0 else "age unknown"

    # Break history
    breaks = zone['breaks']
    break_desc = f"{breaks} historical breaks" if breaks > 0 else "no recorded breaks"

    # Build semantic description
    description = (
        f"Water infrastructure zone with {material_desc}, "
        f"{age_desc}, {break_desc}, "
        f"break history factor {zone['factors']['break_history']}, "
        f"serving {zone['segments']} pipe segments"
    )

    # Generate embedding
    embedding = model.encode(description, normalize_embeddings=True)
    return embedding.astype(np.float32).tobytes(), description

def create_vector_index(client):
    """Create Redis vector search index"""
    try:
        # Drop existing index if it exists
        try:
            client.ft(INDEX_NAME).dropindex()
            print(f"✓ Dropped existing index: {INDEX_NAME}")
        except:
            pass

        # Define schema
        schema = [
            TextField("zone_id"),
            TextField("description"),
            NumericField("risk_score"),
            NumericField("breaks"),
            NumericField("age"),
            NumericField("material"),
            NumericField("lat"),
            NumericField("lon"),
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": VECTOR_DIM,
                    "DISTANCE_METRIC": "COSINE"
                }
            )
        ]

        # Create index
        definition = IndexDefinition(prefix=["break:"], index_type=IndexType.HASH)
        client.ft(INDEX_NAME).create_index(schema, definition=definition)
        print(f"✓ Created vector index: {INDEX_NAME}")

    except Exception as e:
        print(f"✗ Error creating index: {e}")
        sys.exit(1)

def embed_and_store_zones(client, zones, model):
    """Embed all zones and store in Redis"""
    print(f"\nEmbedding {len(zones)} zones...")

    stored = 0
    for i, zone in enumerate(zones):
        # Only embed zones with actual breaks (our training set)
        if zone['breaks'] > 0:
            embedding, description = create_break_embedding(zone, model)

            # Store in Redis
            key = f"break:{zone['id']}"
            client.hset(key, mapping={
                "zone_id": zone['id'],
                "description": description,
                "risk_score": zone['risk'],
                "breaks": zone['breaks'],
                "age": zone['factors']['age'],
                "material": zone['factors']['material'],
                "lat": zone['lat'],
                "lon": zone['lon'],
                "embedding": embedding
            })
            stored += 1

        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(zones)} zones...")

    print(f"✓ Stored {stored} break records with embeddings in Redis")
    return stored

def test_similarity_search(client, zones, model):
    """Test vector similarity search"""
    print("\n" + "="*60)
    print("TESTING VECTOR SIMILARITY SEARCH")
    print("="*60)

    # Find a high-risk zone with breaks
    test_zone = None
    for zone in zones:
        if zone['risk'] >= 80 and zone['breaks'] > 5:
            test_zone = zone
            break

    if not test_zone:
        print("No suitable test zone found")
        return

    print(f"\nTest zone: {test_zone['id']}")
    print(f"  Risk: {test_zone['risk']}, Breaks: {test_zone['breaks']}")
    print(f"  Age: {test_zone['factors']['age']}, Material: {test_zone['factors']['material']}")

    # Create embedding for test zone
    embedding, _ = create_break_embedding(test_zone, model)

    # Search for similar zones
    query = (
        Query(f"*=>[KNN 5 @embedding $vec AS score]")
        .return_fields("zone_id", "description", "risk_score", "breaks", "score")
        .sort_by("score")
        .dialect(2)
    )

    result = client.ft(INDEX_NAME).search(
        query,
        query_params={"vec": embedding}
    )

    print(f"\nTop 5 similar zones:")
    for i, doc in enumerate(result.docs, 1):
        print(f"\n  {i}. Zone {doc.zone_id}")
        print(f"     Similarity: {1 - float(doc.score):.3f}")
        print(f"     Risk: {doc.risk_score}, Breaks: {doc.breaks}")
        print(f"     {doc.description[:80]}...")

def main():
    print("="*60)
    print("BLUE GRID — REDIS VECTOR SEARCH SETUP")
    print("="*60)

    # Load embedding model
    print("\nLoading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✓ Model loaded: all-MiniLM-L6-v2 (384 dimensions)")

    # Connect to Redis
    client = connect_redis()

    # Load zone data
    zones = load_zones_data()

    # Create vector index
    create_vector_index(client)

    # Embed and store zones
    count = embed_and_store_zones(client, zones, model)

    # Test similarity search
    test_similarity_search(client, zones, model)

    print("\n" + "="*60)
    print(f"✓ SETUP COMPLETE")
    print(f"  Indexed {count} break records")
    print(f"  Vector dimension: {VECTOR_DIM}")
    print(f"  Distance metric: COSINE")
    print(f"  Index name: {INDEX_NAME}")
    print("="*60)
    print("\nNext: Start the API server to enable similarity search in the dashboard")
    print("  python redis_api.py")
    print("="*60)

if __name__ == "__main__":
    main()
