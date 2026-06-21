#!/usr/bin/env python3
"""
Blue Grid — Load Water Main Breaks to Redis Vector Database

Loads break records from latest_breaks.json into Redis as vectors
for similarity search using RedisVL.

Run: python3 load_breaks_to_redis.py
"""
import json
import sys
import numpy as np
from datetime import datetime

try:
    import redis
    from redis.commands.search.field import TextField, NumericField, VectorField
    from redis.commands.search.index_definition import IndexDefinition, IndexType
except ImportError as e:
    print(f"ERROR: Missing or incompatible dependencies: {e}")
    print("\nInstall with:")
    print("  pip install 'redis>=5.0.0'")
    print("\nNote: Requires redis-py 5.0+ with search capabilities")
    sys.exit(1)

print("\n" + "="*80)
print("BLUE GRID — LOAD BREAKS TO REDIS VECTOR DATABASE")
print("="*80)

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    redis_url = config.get('redis_url')
    print(f"✓ Loaded Redis URL from config.json")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    sys.exit(1)

# Connect to Redis
try:
    print("\n[1/4] Connecting to Redis...")
    r = redis.from_url(redis_url, decode_responses=True)
    r.ping()
    print(f"      ✓ Connected to Redis")
except Exception as e:
    print(f"      ✗ Redis connection failed: {e}")
    sys.exit(1)

# Load break data
try:
    print("\n[2/4] Loading water main break data...")
    with open('latest_breaks.json', 'r') as f:
        data = json.load(f)

    records = data.get('records', [])
    print(f"      ✓ Loaded {len(records)} break records from latest_breaks.json")
except FileNotFoundError:
    print(f"      ✗ latest_breaks.json not found")
    print(f"      Run: python3 browserbase_agent.py")
    sys.exit(1)

# Create vector embeddings for each break
def create_break_vector(record):
    """
    Create a simple numerical vector from break attributes.
    Vector components: [material_code, age_estimate, diameter, lat, lon]
    """
    # Material encoding (simple categorical to numeric)
    material = str(record.get('ASSET_MATERIAL') or record.get('MATERIAL', '')).upper()
    material_map = {
        'CAST IRON': 1.0,
        'DUCTILE IRON': 0.8,
        'PVC': 0.3,
        'STEEL': 0.9,
        'CONCRETE': 0.6,
        'HDPE': 0.2,
    }
    material_code = material_map.get(material, 0.5)

    # Age estimate (from incident date if available)
    age_estimate = 50.0  # Default
    incident_date = record.get('INCIDENT_DATE') or record.get('DATE')
    if incident_date:
        try:
            date = datetime.fromtimestamp(incident_date / 1000) if incident_date > 10000000000 else datetime.fromisoformat(str(incident_date))
            years_ago = (datetime.now() - date).days / 365.25
            age_estimate = min(years_ago * 2, 100.0)  # Assume older pipes break more
        except:
            pass

    # Diameter (size)
    diameter = 150.0  # Default
    asset_size = record.get('ASSET_SIZE') or record.get('DIAMETER')
    if asset_size:
        try:
            diameter = float(str(asset_size).replace('mm', '').strip())
        except:
            pass

    # Location (lat/lon normalized)
    lat = 43.45  # Default Kitchener
    lon = -80.49
    geom = record.get('geometry', {})
    if geom and geom.get('x') and geom.get('y'):
        lon = geom['x']
        lat = geom['y']

    # Normalize to 0-1 range for vector
    vector = np.array([
        material_code,           # 0-1
        age_estimate / 100.0,    # 0-1
        diameter / 500.0,        # 0-1 (assuming max 500mm)
        (lat - 43.4) * 100,      # Normalized around Kitchener
        (lon + 80.5) * 100       # Normalized around Kitchener
    ], dtype=np.float32)

    return vector.tolist()

# Create index for vector search
INDEX_NAME = "breaks_idx"

try:
    print("\n[3/4] Creating Redis vector search index...")

    # Drop existing index if it exists
    try:
        r.ft(INDEX_NAME).dropindex()
        print(f"      Dropped existing index")
    except:
        pass

    # Create new index with vector field
    schema = (
        TextField("$.street", as_name="street"),
        TextField("$.material", as_name="material"),
        TextField("$.break_type", as_name="break_type"),
        NumericField("$.object_id", as_name="object_id"),
        VectorField(
            "$.vector",
            "FLAT",
            {
                "TYPE": "FLOAT32",
                "DIM": 5,
                "DISTANCE_METRIC": "COSINE",
            },
            as_name="vector"
        ),
    )

    definition = IndexDefinition(prefix=["break:"], index_type=IndexType.JSON)
    r.ft(INDEX_NAME).create_index(schema, definition=definition)
    print(f"      ✓ Created vector search index: {INDEX_NAME}")

except Exception as e:
    print(f"      ✗ Failed to create index: {e}")
    sys.exit(1)

# Load records into Redis
try:
    print("\n[4/4] Loading break records into Redis...")
    loaded_count = 0

    for i, record in enumerate(records):
        # Create vector
        vector = create_break_vector(record)

        # Prepare document
        doc = {
            "object_id": record.get('OBJECTID', i),
            "street": record.get('STREET') or record.get('LOCATION', 'Unknown'),
            "material": record.get('ASSET_MATERIAL') or record.get('MATERIAL', 'Unknown'),
            "break_type": record.get('BREAK_TYPE') or record.get('TYPE', 'Unknown'),
            "status": record.get('STATUS', 'Unknown'),
            "incident_date": record.get('INCIDENT_DATE') or record.get('DATE'),
            "vector": vector
        }

        # Store in Redis as JSON
        key = f"break:{i}"
        r.json().set(key, "$", doc)
        loaded_count += 1

    print(f"      ✓ Loaded {loaded_count} break records into Redis")

except Exception as e:
    print(f"      ✗ Failed to load records: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test vector search
try:
    print("\n" + "="*80)
    print("TESTING VECTOR SEARCH")
    print("="*80)

    # Create a test query vector (cast iron pipe, age 60, diameter 200mm)
    test_vector = np.array([
        1.0,    # Cast iron
        0.6,    # 60 years old
        0.4,    # 200mm diameter
        0.0,    # Center of Kitchener
        0.0     # Center of Kitchener
    ], dtype=np.float32).tolist()

    # Search for similar breaks
    from redis.commands.search.query import Query

    query = (
        Query("*=>[KNN 3 @vector $vec AS score]")
        .return_fields("street", "material", "break_type", "score")
        .sort_by("score")
        .dialect(2)
    )

    results = r.ft(INDEX_NAME).search(query, query_params={"vec": np.array(test_vector, dtype=np.float32).tobytes()})

    print(f"\nTest Query: Cast Iron pipe, 60 years old, 200mm diameter")
    print(f"Found {results.total} similar breaks:\n")

    for i, doc in enumerate(results.docs, 1):
        print(f"  {i}. {doc.street}")
        print(f"     Material: {doc.material}, Type: {doc.break_type}")
        print(f"     Similarity: {float(doc.score):.3f}")
        print()

except Exception as e:
    print(f"✗ Search test failed: {e}")
    import traceback
    traceback.print_exc()

print("="*80)
print("✓ REDIS VECTOR DATABASE READY")
print("="*80)
print(f"Index: {INDEX_NAME}")
print(f"Records: {loaded_count}")
print(f"Vector dimensions: 5 (material, age, diameter, lat, lon)")
print("\nNext steps:")
print("  1. Start redis_api.py to enable vector search endpoint")
print("  2. Dashboard will query similar breaks when viewing pipes")
print("="*80 + "\n")
