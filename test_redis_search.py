#!/usr/bin/env python3
"""
Test Redis vector search end-to-end
"""
import requests
import json

print("\n" + "="*70)
print("TESTING REDIS VECTOR SEARCH")
print("="*70)

# Test query: Cast iron pipe, 65 years old, 200mm diameter
test_query = {
    "material": "Cast Iron",
    "age": 65,
    "diameter": 200,
    "lat": 43.45,
    "lon": -80.49,
    "top_k": 3
}

print(f"\nQuery: {test_query['material']}, {test_query['age']} years old, {test_query['diameter']}mm")
print(f"Finding top {test_query['top_k']} similar breaks...\n")

try:
    response = requests.post(
        'http://localhost:5001/api/similar-breaks',
        json=test_query,
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()

        if data['success']:
            print(f"✓ Found {data['count']} similar breaks:\n")

            for i, brk in enumerate(data['similar_breaks'], 1):
                print(f"{i}. {brk['street']}")
                print(f"   Material: {brk['material']}")
                print(f"   Type: {brk['break_type']}")
                print(f"   Status: {brk['status']}")
                print(f"   Similarity: {brk['similarity']:.3f}")
                print()

            print("="*70)
            print("✓ REDIS VECTOR SEARCH TEST PASSED")
            print("="*70 + "\n")
        else:
            print(f"✗ API returned error: {data.get('error')}")
    else:
        print(f"✗ HTTP {response.status_code}: {response.text}")

except requests.ConnectionError:
    print("✗ Could not connect to http://localhost:5001")
    print("  Make sure redis_api.py is running")
except Exception as e:
    print(f"✗ Error: {e}")
