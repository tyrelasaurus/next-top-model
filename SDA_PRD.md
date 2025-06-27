# Sports Data Aggregator (SDA) — Product Requirements Document (PRD)

## 1. Overview

Build a cross-platform, low-code web application (with optional CLI) that ingests, cleans, consolidates, and serves granular grid-iron football data (NFL, CFL, NCAA). Over time, extend to other sports (hockey, soccer, baseball, basketball, tennis). The user (analyst, hobbyist) will search leagues, fetch historical and live data via APIs and Selenium scrapers, store it in Google Cloud/Drive, and explore it through an intuitive UI or CLI.

## 2. Context & Problem Statement

**Context:**
- No off-the-shelf solution delivers unified, granular sports stats across multiple grid-iron leagues.
- Analysts juggle half-broken APIs, custom scrapers, spreadsheets, and manual merges—error-prone and non-scalable.

**Problems:**
- **Data fragmentation:** Different sources use different IDs, structures, timestamps.
- **Redundant ingests:** Entire seasons get re-pulled daily, wasting bandwidth and compute.
- **Lack of unified identifiers:** Matching “Team A vs. Team B” across API and scraped data is manual.
- **No incremental update:** Every run re-downloads static historical data.
- **Search/UI gaps:** No simple way to drill into per-player, per-play, per-game data.

## 3. Objectives & Success Metrics

**Objectives:**
- **O1:** Centralize team, schedule, game, and player data for NFL, CFL, NCAA
- **O2:** Automate daily delta updates—only fetch new games/stats
- **O3:** Expose a searchable, filterable UI and lightweight CLI
- **O4:** Ensure data integrity: dedupe, normalize timestamps, unify IDs
- **O5:** Provide JSON/Parquet exports to Google Drive/Cloud Storage

**Metrics:**
- **Time to first dataset ingest (MVP):** < 2 hours
- **Daily update runtime (delta-only):** < 15 min
- **Data completeness:** ≥ 95% of official stats fields
- **UI search latency:** < 300 ms

## 4. Key Users & Stories

- **Data Analyst:** “I want to pull a complete NFL 2023 season dataset, then query every rushing play over 20 yards.”
- **Fantasy Enthusiast:** “I want player career stats and team travel distances to build a predictive model.”
- **Coach/Researcher:** “I need historical head-to-head matchups between Team X and Team Y with stadium weather data.”
- **CLI Power-User:** “I prefer scripting daily pulls and custom exports in my terminal.”

## 5. Solution Overview

**Web App + API + CLI**
- Central admin console: configure leagues, API keys, scrape rules, update schedules
- Dashboard: status of last ETL runs, error logs, record counts
- Data Explorer: filter by league/season/team/player, visualize results
- RESTful API & CLI (built with ClaudeCode CLI) for advanced querying and scripting

**Modular ETL Pipelines**
- Source Connectors: API modules (e.g. TheSportsDB, custom scrapers for Pro Football Reference/ESPN)
- Transformer: pandas-style pipeline (field mappings, type casts, dedupe, UID assignment)
- Loader: writes to Postgres (hosted on Google Cloud SQL) + JSON backups on GCS/Drive

**Unified Schema & UIDs**
- `teams` (team_uid, league, city, name, stadium_capacity, lat, lon)
- `games` (game_uid, league, season, week, home_team_uid, away_team_uid, datetime, location)
- `players` (player_uid, name, position, birthdate, college, team_uid_history JSON)
- `player_stats` (stat_uid, player_uid, game_uid, stat_type, value)

## 6. Functional Requirements

### 6.1 Data Ingestion

- **R6.1.1:** Support API pulls with pagination and rate-limit handling (TheSportsDB as primary, scrapers for supplemental data)
- **R6.1.2:** Support Selenium/BS4 recipes keyed to CSS selectors for non-API sources
- **R6.1.3:** Incremental fetch logic: track last‐modified timestamps or max game_uid per source

### 6.2 Data Transformation

- **R6.2.1:** Field normalization (e.g. “PTS” → points_scored)
- **R6.2.2:** Type enforcement (dates → ISO 8601, numeric casts)
- **R6.2.3:** Deduplication by UID + source tag
- **R6.2.4:** Cross-source matching: merge records on composite keys (date+teams+venue)

### 6.3 Data Storage & Export

- **R6.3.1:** Primary store in Postgres (Google Cloud SQL)
- **R6.3.2:** Daily export of raw JSON/CSV to GCS/Drive
- **R6.3.3:** Backups retention: 90 days on GCS + local snapshots

### 6.4 Search & UI

- **R6.4.1:** Full-text & facet filtering on all text/numeric fields
- **R6.4.2:** Table, chart and JSON views
- **R6.4.3:** Prebuilt queries: “Top 10 rushers per season”, “Biggest away upsets”

### 6.5 CLI

- **R6.5.1:** `sda sync [league] [--season YEAR]`
- **R6.5.2:** `sda query --sql "SELECT * FROM games WHERE ..."`
- **R6.5.3:** Export flags: `--format csv/json/parquet`

## 7. Non-Functional Requirements

- **Scalability:** Handle 5M+ records without UI slowdown
- **Reliability:** 99.9% ETL success rate; retry on transient failures
- **Security:** Secrets vault (API keys), OAuth for Google Drive
- **Configurable:** Developer can add new league connectors via JSON config
- **Documentation:** Auto-generated OpenAPI spec + CLI man pages

## 8. Data Update Strategy

- **Daily Scheduled Trigger:** Run “delta” pipelines at 2 AM UTC
- **Delta Detection:**
  - APIs: use `updated_since` params when available
  - Scrapers: compare newly scraped match list against `games.game_uid`
- **Full-Backfill Jobs:** Run on demand per league/season (takes hours)
- **Change Logs:** Write per‐record audit logs (`created_at`, `updated_at`, `source`)

## 9. Architecture Diagram (ASCII)

```
┌───────────┐      ┌────────────┐    ┌─────────┐
│ Scheduler │─────▶│ ETL Runner │───▶│ Postgres│
└───────────┘      └────────────┘    └─────────┘
                               │          │
                               ▼          ▼
                        ┌────────┐    ┌──────────┐
                        │  GCS   │    │  Web UI  │
                        └────────┘    └──────────┘
                              ▲            ▲
                              │            │
                        ┌──────────┐    ┌──────┐
                        │  CLI     │    │ API  │
                        └──────────┘    └──────┘
```

## 10. Tech Stack

- **Backend:** Python 3.10, FastAPI, SQLAlchemy, pandas
- **Scraping:** Selenium + BeautifulSoup (fallback: Playwright)
- **Scheduler:** cronjobs in Airflow or Cloud Scheduler
- **Database:** Postgres (Cloud SQL)
- **Storage:** Google Cloud Storage + Drive SDK
- **Frontend:** React + Material UI + Chart.js
- **CLI:** Click (Python) via ClaudeCode templates

## 11. Milestones & Roadmap

| Milestone            | Description                                      | ETA      |
|----------------------|--------------------------------------------------|----------|
| **M1: MVP Ingestion**| NFL historical & delta pipeline + basic UI       | 6 weeks  |
| **M2: Expand Leagues**| CFL + NCAA ingestion, CLI commands              | +4 weeks |
| **M3: UI Enhancements**| Advanced filters, charting, save/query library | +3 weeks |
| **M4: Cross-Sport**  | Add hockey & soccer connectors (config-driven)   | +6 weeks |
| **M5: Power Rankings**| Analytics module: compute team/player ratings   | +4 weeks |

## 12. Open Questions & Next Steps

| Question         | Decision/Action |
|------------------|-----------------|
| Auth & Users     | Single-user only. No multi-user roles required for MVP or future roadmap. |
| Rate Limits      | Use paid TheSportsDB API as primary source; supplement with web scraping (Pro Football Reference, ESPN) as needed. Paid tier is sufficient for solo analyst; backup data extraction via scraping if API unavailable or insufficient. |
| Granularity      | Ingest and store full game-level and player-level stats only (box scores, player stats, game reports). Play-by-play and drive-level not required for MVP. |
| Extensibility    | Modular architecture to allow developer-led addition of new sports, leagues, or stat types via config files and source modules; end user does not manage connectors. |

## Bibliography / References

- TheSportsDB API Docs & Pricing
- Pro Football Reference
- ESPN API (unofficial/reverse engineered)
- Singer.io – Modular ETL Connectors
- ETL Patterns with Airflow

