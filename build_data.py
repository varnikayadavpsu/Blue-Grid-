#!/usr/bin/env python3
"""
Blue Grid — Kitchener water-infrastructure risk pipeline (Half A).

Run:  python build_data.py
Output: zones.json   (the dashboard reads ONLY this file)

What it does, in order:
  1. SCHEMA CHECK   — pull 5 rows from each endpoint, print field names.
  2. PULL           — full Water Mains snapshot + full Water Main Breaks history.
  3. REPROJECT      — both to EPSG:4326. PRINT bounding box (must be ~ Kitchener).
  4. JOIN           — snap each break to nearest main = label. PRINT match count.
  5. SCORE          — transparent weighted risk per segment -> aggregate to zones.
  6. MODEL          — RandomForest 80/20, PRINT one validation number.
  7. EXPORT         — zones.json.

The three PRINTS marked [VERIFY] are what catch silent failures. Eyeball them.

Dependencies:  pip install requests geopandas pandas scikit-learn shapely numpy
If geopandas is a pain to install, see the NOTE at the bottom — there is a
no-geopandas fallback path that still produces a usable zones.json.
"""

import json
import sys
import math

# ----------------------------------------------------------------------
# STEP 0 — CONFIG.  >>> PASTE YOUR REAL FEATURESERVER URLS HERE <<<
# Find them on the Kitchener dataset page: "I want to use this" / "View API Resources".
# They end in /FeatureServer/<n>.  Leave the trailing /<layer-number> off here;
# we add /query below.
# ----------------------------------------------------------------------
MAINS_URL  = "https://services1.arcgis.com/qAo1OsXi67t7XgmS/ArcGIS/rest/services/Water_Mains/FeatureServer/0"
BREAKS_URL = "https://services1.arcgis.com/qAo1OsXi67t7XgmS/ArcGIS/rest/services/Water_Main_Breaks/FeatureServer/0"

KITCHENER_LON, KITCHENER_LAT = -80.49, 43.45  # expected center, for the bbox check

# ----------------------------------------------------------------------
def fetch_arcgis(base_url, where="1=1", out_fields="*", max_records=None, count_only=False):
    """Pull features from an ArcGIS FeatureServer layer as GeoJSON.
    Handles pagination automatically."""
    import requests
    params = {
        "where": where,
        "outFields": out_fields,
        "f": "geojson",
        "outSR": 4326,            # ask the server to return WGS84 directly
    }
    if count_only:
        params.update({"returnCountOnly": "true", "f": "json"})
        r = requests.get(base_url + "/query", params=params, timeout=60)
        return r.json().get("count")
    if max_records:
        params["resultRecordCount"] = max_records

    features = []
    offset = 0
    while True:
        params["resultOffset"] = offset
        r = requests.get(base_url + "/query", params=params, timeout=120)
        r.raise_for_status()
        gj = r.json()
        batch = gj.get("features", [])
        features.extend(batch)
        if max_records or len(batch) == 0 or not gj.get("exceededTransferLimit"):
            break
        offset += len(batch)
    return {"type": "FeatureCollection", "features": features}


def schema_check():
    print("=" * 60)
    print("STEP 1 — SCHEMA CHECK (5 sample rows per layer)")
    print("=" * 60)
    for name, url in [("WATER MAINS", MAINS_URL), ("WATER MAIN BREAKS", BREAKS_URL)]:
        try:
            gj = fetch_arcgis(url, max_records=5)
            feats = gj["features"]
            print(f"\n{name}: pulled {len(feats)} sample rows")
            if feats:
                props = feats[0]["properties"]
                print(f"  FIELDS: {list(props.keys())}")
                print(f"  SAMPLE: {json.dumps(props, default=str)[:400]}")
        except Exception as e:
            print(f"\n{name}: FAILED — {e}")
            print("  >>> Check the URL. Test in a browser: <url>/query?where=1=1&outFields=*&resultRecordCount=5&f=json")
    print()


# ----------------------------------------------------------------------
# Material fragility lookup — tune to whatever values the schema actually shows.
FRAGILITY = {
    "CAST IRON": 1.0, "CI": 1.0, "UNLINED": 0.95,
    "DUCTILE IRON": 0.5, "DI": 0.5,
    "PVC": 0.2, "HDPE": 0.15, "CONCRETE": 0.6, "STEEL": 0.55,
}
def material_fragility(mat):
    if not mat:
        return 0.5
    m = str(mat).upper()
    for key, val in FRAGILITY.items():
        if key in m:
            return val
    return 0.5  # unknown -> neutral


def pick_field(props, candidates):
    """Find the first matching field name (case-insensitive) from candidates."""
    lower = {k.lower(): k for k in props.keys()}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def main():
    if "PASTE_" in MAINS_URL or "PASTE_" in BREAKS_URL:
        print("!! Set MAINS_URL and BREAKS_URL at the top of this file first.")
        print("!! Running schema_check() will still fail without them.")
        print("!! Tip: run the schema check first to discover the real field names.\n")

    schema_check()

    print("=" * 60)
    print("STEP 2-5 — PULL, JOIN, SCORE  (needs geopandas)")
    print("=" * 60)
    try:
        import geopandas as gpd
        import pandas as pd
        import numpy as np
        from shapely.geometry import shape
    except ImportError:
        print("geopandas/pandas not installed. Run: pip install geopandas pandas scikit-learn shapely numpy")
        print("See the no-geopandas NOTE at the bottom of this file for a fallback.")
        return

    # --- PULL ---
    print("Pulling full mains snapshot + full breaks history (may take a minute)...")
    mains = gpd.GeoDataFrame.from_features(fetch_arcgis(MAINS_URL)["features"], crs="EPSG:4326")
    breaks = gpd.GeoDataFrame.from_features(fetch_arcgis(BREAKS_URL)["features"], crs="EPSG:4326")
    print(f"  mains:  {len(mains)} segments")
    print(f"  breaks: {len(breaks)} recorded events")

    # --- REPROJECT to a metric CRS for distance, keep 4326 copy for export ---
    # UTM zone 17N (EPSG:32617) is correct for Kitchener.
    mains_m = mains.to_crs(32617)
    breaks_m = breaks.to_crs(32617)

    # [VERIFY 1] bounding box in lat/lon — must straddle Kitchener
    b = mains.total_bounds  # minx, miny, maxx, maxy in 4326
    print("\n[VERIFY 1] Mains bounding box (lon/lat):")
    print(f"   lon {b[0]:.3f} to {b[2]:.3f}   lat {b[1]:.3f} to {b[3]:.3f}")
    ok = (b[0] < KITCHENER_LON < b[2]) and (b[1] < KITCHENER_LAT < b[3])
    print(f"   {'OK — contains Kitchener center' if ok else '!! NOT around Kitchener — projection likely wrong'}")

    # --- JOIN: each break -> nearest main segment = label broke=1 ---
    joined = gpd.sjoin_nearest(breaks_m, mains_m.reset_index().rename(columns={"index": "main_id"}),
                               how="left", max_distance=50, distance_col="dist_m")
    matched = joined["main_id"].notna().sum()
    print(f"\n[VERIFY 2] Break-to-main matches: {matched} of {len(breaks)} breaks snapped to a segment within 50m")
    print(f"   {'OK' if matched > 0 else '!! ZERO matches — the join failed silently. Check CRS / geometry.'}")

    # break count per segment
    break_counts = joined.groupby("main_id").size()
    mains_m = mains_m.reset_index().rename(columns={"index": "main_id"})
    mains_m["break_count"] = mains_m["main_id"].map(break_counts).fillna(0)
    mains_m["broke"] = (mains_m["break_count"] > 0).astype(int)

    # --- FEATURES for the score (auto-detect field names) ---
    props0 = mains.iloc[0].to_dict()
    fld_year = pick_field(props0, ["INSTALL_DATE", "YEAR_INSTALLED", "INSTALLYEAR", "INSTALLED", "YEARLAID", "DATE_LAID"])
    fld_mat  = pick_field(props0, ["MATERIAL", "PIPE_MATERIAL", "MAT", "MATL"])
    fld_dia  = pick_field(props0, ["DIAMETER", "DIA", "SIZE", "NOMINAL_DIAMETER"])
    print(f"\nDetected fields -> year:{fld_year}  material:{fld_mat}  diameter:{fld_dia}")

    import datetime
    this_year = datetime.date.today().year
    def to_age(v):
        if v is None: return 60
        try:
            y = int(str(v)[:4])
            if 1850 < y <= this_year: return this_year - y
        except: pass
        return 60
    age = mains_m[fld_year].map(to_age) if fld_year else pd.Series([60]*len(mains_m))
    age_norm = (age / max(age.max(), 1)).clip(0, 1)
    frag = mains_m[fld_mat].map(material_fragility) if fld_mat else pd.Series([0.5]*len(mains_m))
    hist = (mains_m["break_count"] / max(mains_m["break_count"].max(), 1)).clip(0, 1)
    flood = pd.Series([0.2]*len(mains_m))  # placeholder; wire a flood layer here if time allows

    # --- TRANSPARENT SCORE ---
    score = 100 * (0.35*age_norm + 0.25*frag + 0.25*hist + 0.15*flood)
    mains_m["risk"] = score.round().clip(0, 100).astype(int)
    mains_m["age"] = age.values
    mains_m["frag"] = (frag*100).round().astype(int)
    mains_m["histn"] = (hist*100).round().astype(int)

    # --- MODEL (validation proof-point) ---
    print("\n" + "=" * 60); print("STEP 6 — MODEL VALIDATION"); print("=" * 60)
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score
        X = pd.DataFrame({"age": age.values, "frag": frag.values,
                          "dia": pd.to_numeric(mains_m[fld_dia], errors="coerce").fillna(0) if fld_dia else 0})
        y = mains_m["broke"].values
        if y.sum() >= 10 and (y == 0).sum() >= 10:
            Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
            clf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
            clf.fit(Xtr, ytr)
            proba = clf.predict_proba(Xte)[:, 1]
            auc = roc_auc_score(yte, proba)
            # top-quartile capture: of held-out breaks, how many land in top 25% risk?
            te = pd.DataFrame({"p": proba, "y": yte})
            thresh = te["p"].quantile(0.75)
            capture = te[te["y"] == 1]["p"].ge(thresh).mean()
            print(f"[VERIFY 3] Held-out ROC-AUC: {auc:.3f}")
            print(f"[VERIFY 3] Top-quartile capture of real breaks: {capture*100:.0f}%")
            print(f"   PITCH LINE: \"the model ranks {capture*100:.0f}% of streets that actually broke in the top quartile of risk\"")
        else:
            print(f"   Not enough labeled breaks to validate ({y.sum()} positives). Score still valid; report it qualitatively.")
    except ImportError:
        print("   scikit-learn not installed — skipping model. The transparent score is unaffected.")

    # --- AGGREGATE TO ZONES & EXPORT ---
    # Simple zoning: round lat/lon to a grid cell. Swap for real ward polygons if you have them.
    cent = mains.geometry.centroid
    mains_m["zone"] = [f"{round(la,2)}_{round(lo,2)}" for la, lo in zip(cent.y, cent.x)]
    agg = mains_m.groupby("zone").agg(
        risk=("risk", "mean"), age=("age", "mean"), frag=("frag", "mean"),
        histn=("histn", "mean"), breaks=("break_count", "sum"), segments=("main_id", "count"),
    ).reset_index()
    zlat = mains_m.groupby("zone").apply(lambda g: cent.loc[g.index].y.mean())
    zlon = mains_m.groupby("zone").apply(lambda g: cent.loc[g.index].x.mean())

    # --- PERCENTILE-BASED RESCALING (relative-to-Kitchener normalization) ---
    # The raw weighted score compresses into a narrow band. To make the dashboard useful,
    # rescale final zone scores to 0-100 based on their rank within Kitchener's actual distribution.
    # This is NOT invented data — it's a relative ranking of real risk within this city's infrastructure.
    # Using a power transform (exponent < 1) to create natural spread with visible separation at the top.
    raw_scores = agg["risk"].values
    ranks = raw_scores.argsort().argsort()  # 0 = lowest risk, n-1 = highest
    normalized_ranks = ranks / max(ranks.max(), 1)  # 0 to 1
    # Power transform: spread upper scores, compress lower scores
    # Exponent 0.65 creates good separation; scale to max ~94 to avoid artificial "100"
    rescaled = (normalized_ranks ** 0.65) * 95
    agg["risk"] = rescaled.round().clip(0, 100).astype(int)

    zones = []
    for _, row in agg.iterrows():
        z = row["zone"]
        zones.append({
            "id": z,
            "lat": round(float(zlat[z]), 5), "lon": round(float(zlon[z]), 5),
            "risk": int(round(row["risk"])),
            "factors": {"age": int(row["age"]), "material": int(row["frag"]),
                        "break_history": int(row["histn"]), "flood": 20},
            "breaks": int(row["breaks"]), "segments": int(row["segments"]),
        })
    zones.sort(key=lambda z: -z["risk"])

    # Print risk distribution by band
    low = sum(1 for z in zones if z["risk"] <= 30)
    medium = sum(1 for z in zones if 31 <= z["risk"] <= 60)
    high = sum(1 for z in zones if 61 <= z["risk"] <= 80)
    critical = sum(1 for z in zones if z["risk"] >= 81)
    print(f"\n{'='*60}")
    print("RISK DISTRIBUTION (relative to Kitchener infrastructure)")
    print(f"{'='*60}")
    print(f"  Low (0-30):       {low:3d} zones")
    print(f"  Medium (31-60):   {medium:3d} zones")
    print(f"  High (61-80):     {high:3d} zones")
    print(f"  Critical (81+):   {critical:3d} zones")
    print(f"  Top zone risk:    {zones[0]['risk'] if zones else 'n/a'}")

    with open("zones.json", "w") as f:
        json.dump({"city": "Kitchener, ON", "zones": zones}, f, indent=2)
    print(f"\nEXPORTED zones.json — {len(zones)} zones")
    print("Done. The dashboard reads zones.json.")


if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------
# NOTE — no-geopandas fallback:
# If geopandas won't install in time, do the join the slow-but-simple way:
#   - pull both layers as GeoJSON (the fetch_arcgis function works without geopandas)
#   - for each break point, loop over main segments and compute distance with a
#     plain haversine; nearest within ~50m gets the label.
# It's O(breaks x mains) so slower, but Kitchener's data is small enough to brute-force.
# Ask Claude Code: "rewrite the join without geopandas using haversine distance."
# ----------------------------------------------------------------------
