# Snapchat Map Scraper KC — Mentor / Operational Fork

> **Status:** `[ARCHIVED]` — Pre-ChatGPT Open-Source Adaptation & Local Media Scraper (June 2022) — No Longer Maintained  
> **Original Upstream Repository:** [`nemec/snapchat-map-scraper`](https://github.com/nemec/snapchat-map-scraper) by Dan Nemec  
> **Stack:** Python 3, SQLite, Requests, Requests-Futures, Snap Map HTTP Endpoints

This repository is an archived **June 2022 operational fork** of Dan Nemec's open-source `snapchat-map-scraper`. It was adapted for collecting, archiving, reviewing, and classifying geographically targeted public Snap Map media in the Kansas City area.

---

## Provenance & Historical Context

This repository is not software written from scratch. It is a preserved fork demonstrating a real-world software engineering workflow from the pre-generative-AI era (~5 months before ChatGPT was released in November 2022):
1. **Discovering Open Source:** Finding an existing tool addressing an undocumented external API.
2. **Code Comprehension & Deployment:** Understanding unfamiliar architecture and deploying it locally against live geospatial targets.
3. **Operational Diagnosis & Patching:** Encountering real-world duplication bugs during media review workflows, diagnosing the root cause, and patching the system (`SELECT DISTINCT` query fix in commit `36f2e82` on June 14, 2022).

---

## How It Worked

```text
Target Coordinates (Lat / Long / Radius)
           │
           ▼
Snap Map Web Service (getLatestTileSet & getPlaylist)
           │
           ▼
Public Geographic Stories / Media JSON
           │
           ▼
Download Media, Preview & Overlay Assets
           │
           ▼
SQLite Catalog (Deduplication & Polling History)
           │
           ▼
CLI Review, Classification & Media Export
```

- Polled target geographic points with jitter/perturbation.
- Persisted metadata, timestamps, locations, and downloaded media files into a local SQLite database.
- Interactive CLI review interface for filtering, classifying, and exporting clips.

---

## Why Development Has Ended

- **External Interface Retired:** Snapchat removed the public web version of Snap Map and transitioned it to mobile-only, closing the undocumented web acquisition surface.
- **Contractual & Platform Restrictions:** Current Snap terms explicitly prohibit automated scraping, and no general-purpose public geographic search API is offered.
- **No Resumption Planned:** Preserved as an immutable historical artifact. No dependency modernization or reverse-engineering of private mobile APIs will occur.
