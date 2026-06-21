# Blue Grid — Project Context

## What this is
Blue Grid is a civic water-infrastructure risk dashboard for the UC Berkeley AI Hackathon 2026.
Solo build, due Sunday 11am. Built in Claude Code (this counts toward the Anthropic prize).

**One-line pitch:** Kitchener logs every water main break it has ever had, so we trained on real
failures, validated against held-out breaks, and turned it into a command center that tells the
city exactly where to inspect next.

## The honest framing (do not break this)
- We do NOT claim to predict the exact pipe and hour of a break.
- We produce a **validated, transparent, zone-level risk ranking**, and we say so.
- Directional + validated + honest beats over-claimed accuracy.

## Data sources (City of Kitchener Open Data — ArcGIS Hub, public, no auth)
1. **Water Mains** — asset inventory: geometry, diameter, material, install date/age, length. Snapshot once.
2. **Water Main Breaks** — ground truth: full historical break events with location. THIS IS THE LABEL SET.
   Pull the FULL history, not one day.
3. (Optional) elevation / flood layer — enrichment only, cut if time-tight.

The mains+breaks pairing is the whole edge: real assets + real failures = real prediction.

## Risk model
Transparent weighted score per pipe segment, aggregated to zones:

    risk = 0.35*age_norm + 0.25*material_fragility + 0.25*break_history_proximity + 0.15*flood_exposure

Scaled 0-100. Buckets: 0-30 Low, 31-60 Medium, 61-80 High, 81-100 Critical.
material_fragility: cast iron / unlined = high, ductile / PVC = low.

Two layers, kept separate ON PURPOSE:
- **Transparent score** drives the live dashboard (explainable, never breaks).
- **Random Forest** (scikit-learn) trained on labeled segments, 80/20 split, is the VALIDATION
  proof-point — one number: "ranks the streets that actually broke in the top quartile." NOT a live-demo dependency.

## Architecture — two decoupled halves
- **Half A (offline notebook):** pull -> reproject -> spatial join (break -> nearest main = label)
  -> score -> export `zones.json` -> train model. Run a few times, freeze output.
- **Half B (dashboard):** reads ONLY zones.json. Never runs geo code. If Half A breaks, dashboard
  still demos on seeded data.

## THREE VERIFICATION PRINTS (non-negotiable — they catch silent failures)
1. Bounding box after reproject — must be ~ lon -80.5, lat 43.45 (Kitchener). Else projection wrong.
2. Break-to-main match count after join — if 0, the join silently failed.
3. Model validation number on held-out breaks.

## Sponsor integrations (all genuine — would use even without the prize)
- **Anthropic (anchor):** built in Claude Code; live "generate action plan" feature calls Claude
  to produce a 72-hour inspection plan when a zone is clicked.
- **Redis (~1.5h):** vector search over historical breaks — "find segments similar to ones that failed."
- **Browserbase (~1.5h):** an agent that pulls the Kitchener portal / fetches fresh break reports.

Do NOT add more sponsors. Three is the cap. Everything else = "future integrations" slide.

## Dashboard design
- Dark command-center theme. Background deep slate/ink (#1A2B3A).
- Water teal (#0F6E56 -> #1D9E75) = low risk. Hydrant red (#A32D2D -> #E24B4A) = critical. Amber mid.
- Monospace for all operational numbers (reads like a real ops console).
- Signature element = the risk map. Spend boldness there, keep everything else quiet.
- Panels: KPI banner (animate up) / risk map (click to select) / explain panel (4 factor bars that
  sum to the score) / priority queue (risk x population) / action-plan button (live AI).
- Single-file HTML, no build step — must open directly in a browser.

## Build order (do NOT skip ahead)
1. Schema check — pull 5 rows from each endpoint, print field names. Build on real fields, not assumed.
2. Data pipeline — the Half A notebook with the 3 verification prints.
3. Dashboard — Half B, loads zones.json.
4. Sponsor adds — Redis, then Browserbase.
5. One "wow" feature if core solid — time-machine slider (historical breaks -> predicted future).
6. Pitch + RECORD A BACKUP VIDEO of the working demo.

## Hard deadlines (from hacker guide)
- Devpost DRAFT with project name + you as team: by Sat MIDNIGHT (only guarantee of being judged).
- Submit: by Sun 11am (edits lock at noon).
- Judging: Sun 1-3pm, 4-min table pitch.
