# Blue Grid

**Finding the water pipes most likely to break — before they break.**

Built for UC Berkeley AI Hackathon 2026.

🔗 **Live demo:** https://blue-grid-kitchener.vercel.app/
📦 **Repo:** https://github.com/varnikayadavpsu/Blue-Grid-

## What it does

Every year, water pipes break, flood streets, and waste millions of litres of clean water. Cities usually only find out after a pipe bursts.

Blue Grid changes that. It uses a city's own open data — both its full list of pipes and its complete history of past breaks — to find the pipes most likely to fail next, and gives crews a clear action plan to fix them first.

It shows a city's whole pipe network on an interactive map, colored by risk. Click any pipe to see its risk score, the factors behind it, an AI action plan, and a plain-English explanation of why it's risky.

## How it works

We started with two real datasets from the City of Kitchener's open data portal: the **Water Mains** inventory (2,000 pipes with real material, install year, and size) and the **Water Main Breaks** history (every break the city has recorded).

We matched the breaks to pipes by location, then trained a model that scores every pipe on four factors:

- **Age (35%)** — older pipes are riskier
- **Material (25%)** — cast iron vs. ductile iron vs. PVC, etc.
- **Break history (25%)** — past failures nearby
- **Flood exposure (15%)**

The model ranks all 2,000 pipes by risk and shows them on the map.

## Validation

We tested the model against real outcomes on held-out data:

- **ROC-AUC: 0.73**
- **57% of pipes that actually broke** land in our highest-risk quartile

It's not guessing — it's grounded in what really happened.


## Sponsor integrations

**Anthropic (Claude)** — Powers the live "Generate Action Plan" and "Explain This Pipe" features. Claude takes a pipe's real risk factors and writes a concise, prioritized inspection plan. Deployed live on Render.

**Browserbase** — A cloud browser agent fetches live water main break records straight from Kitchener's open data portal, keeping the data current. Working and live.


## Tech stack

**Frontend:** Single-file HTML, Leaflet + OpenStreetMap, warm editorial theme. Deployed on **Vercel**.

**Backend:** Python data pipeline (geopandas, scikit-learn, RandomForest). Flask AI proxy deployed on **Render**.

**Data:** City of Kitchener Open Data (ArcGIS FeatureServer) — Water Mains + Water Main Breaks.

## Future implementation

Blue Grid today finds *which* pipes are most at risk. Here's where it goes next:

**Weather and climate data.** The biggest near-term upgrade. Freeze-thaw cycles are one of the leading causes of water main breaks in cold climates — when the ground freezes and thaws, it shifts and stresses pipes until they crack. By adding temperature and weather data to the model, Blue Grid could factor in seasonal risk and flag pipes that are vulnerable heading into winter.

**From "which" to "when."** Right now we rank risk. The next step is adding a timing dimension — using install dates, break intervals, and weather patterns to estimate failure *windows*, not just relative risk. This would move the tool from "inspect these first" toward "inspect these before this season."

**Any city, not just Kitchener.** The method works anywhere with open pipe and break data. The pipeline is built to ingest a city's datasets, match them, and score automatically — so onboarding a new city is mostly a matter of pointing it at their open data portal.

**Cost and impact modeling.** Connecting risk scores to repair costs and the cost of failure (water lost, road damage, emergency repairs) would let cities prioritize not just by risk, but by dollars and water saved.

**Continuous live updates.** The Browserbase ingestion agent already pulls fresh break data. Scheduling it to run automatically would keep the risk model current as new failures get logged — a living system rather than a one-time snapshot.
