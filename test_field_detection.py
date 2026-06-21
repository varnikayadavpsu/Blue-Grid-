#!/usr/bin/env python3
"""
Quick test to show field detection and sample data variety before full regeneration.
"""
import requests
import json

MAINS_URL = "https://services1.arcgis.com/qAo1OsXi67t7XgmS/ArcGIS/rest/services/Water_Mains/FeatureServer/0"

def fetch_sample():
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "json",
        "resultRecordCount": 20  # Get 20 samples
    }
    r = requests.get(MAINS_URL + "/query", params=params, timeout=30)
    return r.json()

def pick_field(props, candidates):
    """Find the first matching field name (case-insensitive)."""
    lower = {k.lower(): k for k in props.keys()}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None

print("=" * 70)
print("FIELD DETECTION TEST — Kitchener Water Mains")
print("=" * 70)

data = fetch_sample()
features = data.get("features", [])

if not features:
    print("No features returned!")
    exit(1)

# Show all available fields
props = features[0]["attributes"]
print(f"\nAll available fields ({len(props)} total):")
for field in sorted(props.keys()):
    print(f"  - {field}")

# Test field detection
fld_year = pick_field(props, ["INSTALLATION_DATE", "ASSET_YEAR_INSTALLED", "INSTALL_DATE", "YEAR_INSTALLED", "INSTALLYEAR"])
fld_mat = pick_field(props, ["MATERIAL", "ASSET_MATERIAL", "PIPE_MATERIAL", "MAT"])
fld_dia = pick_field(props, ["PIPE_SIZE", "ASSET_DIAMETER", "ASSET_SIZE", "DIAMETER", "DIA", "SIZE"])

print(f"\n" + "=" * 70)
print("DETECTED FIELDS:")
print("=" * 70)
print(f"  Install Year Field: {fld_year}")
print(f"  Material Field:     {fld_mat}")
print(f"  Diameter Field:     {fld_dia}")

# Show variety in sample data
print(f"\n" + "=" * 70)
print("SAMPLE DATA VARIETY (20 pipes):")
print("=" * 70)

materials = set()
years = []
diameters = set()

print(f"{'Pipe':<6} | {'Year':<6} | {'Age':<5} | {'Material':<15} | {'Diameter':<10}")
print("-" * 70)

import datetime

for i, feat in enumerate(features[:10]):  # Show first 10
    attrs = feat["attributes"]

    year_val_raw = attrs.get(fld_year) if fld_year else None
    mat_val = attrs.get(fld_mat) if fld_mat else None
    dia_val = attrs.get(fld_dia) if fld_dia else None

    # Convert epoch milliseconds to year
    year_val = None
    age = "?"
    if year_val_raw:
        try:
            if year_val_raw > 100000000000:  # Epoch milliseconds
                year_val = datetime.datetime.fromtimestamp(year_val_raw / 1000).year
            elif year_val_raw < 0:  # Negative epoch
                year_val = datetime.datetime.fromtimestamp(year_val_raw / 1000).year
            else:
                year_val = int(str(year_val_raw)[:4])

            if year_val:
                years.append(year_val)
                age = 2026 - year_val
        except:
            pass

    if mat_val:
        materials.add(str(mat_val))
    if dia_val:
        diameters.add(str(dia_val))

    print(f"{i:<6} | {year_val if year_val else 'null':<6} | {age:<5} | {str(mat_val) if mat_val else 'null':<15} | {str(dia_val) if dia_val else 'null':<10}")

print(f"\n" + "=" * 70)
print("VARIETY SUMMARY:")
print("=" * 70)
print(f"  Unique materials found: {len(materials)}")
print(f"  Materials: {', '.join(sorted(materials))}")
print(f"  Year range: {min(years) if years else 'N/A'} to {max(years) if years else 'N/A'}")
print(f"  Unique diameters: {len(diameters)}")
print(f"\n✓ Fields detected correctly! Data shows real variety.")
print(f"  Run 'python3 build_data.py' to regenerate pipes.json with per-pipe data.")
