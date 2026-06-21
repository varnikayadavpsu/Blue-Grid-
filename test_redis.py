#!/usr/bin/env python3
"""
Minimal Redis connectivity test
"""
import json
import sys

try:
    import redis
except ImportError as e:
    print(f"ERROR: Missing redis package: {e}")
    print("\nInstall with:")
    print("  pip install 'redis>=5.0.0'")
    sys.exit(1)

print("\n" + "="*60)
print("REDIS CONNECTIVITY TEST")
print("="*60)

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    redis_url = config.get('redis_url')
    print(f"✓ Loaded redis_url from config.json")
    print(f"  URL: {redis_url[:30]}...")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    sys.exit(1)

try:
    # Connect to Redis
    print("\nConnecting to Redis...")
    r = redis.from_url(redis_url)

    # Test set/get
    test_key = 'bluegrid:test'
    test_value = 'connection_successful'

    r.set(test_key, test_value)
    result = r.get(test_key)

    if result and result.decode('utf-8') == test_value:
        print(f"✓ Redis connected")
        print(f"  Test key set/get: SUCCESS")

        # Clean up
        r.delete(test_key)
        print(f"  Test key deleted")

        print("\n" + "="*60)
        print("✓ REDIS CONNECTION TEST PASSED")
        print("="*60 + "\n")
    else:
        print(f"✗ Set/get test failed")
        sys.exit(1)

except redis.ConnectionError as e:
    print(f"\n✗ Redis connection failed: {e}")
    print(f"   Check if Redis server is running and URL is correct")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")
    sys.exit(1)
