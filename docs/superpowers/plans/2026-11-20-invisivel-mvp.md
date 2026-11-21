# INVISIVEL — Implementation Plan

> **For agentic workers:** use superpowers:executing-plans. The user explicitly requested autonomous implementation without questions or approval gates.

**Goal:** deliver the documented civic territorial MVP, runnable locally, with real official data and persistent moderated participation.

**Architecture:** React/TypeScript/Vite PWA consumes a versioned FastAPI API. SQLAlchemy supports local SQLite and production PostgreSQL; PostGIS/pg_trgm migrations support geospatial deployment. Public official datasets are ingested into durable cache, with reference dates, provenance and explicit gaps.

**Tech Stack:** React, TypeScript, Vite, Tailwind, Lucide, React Router, TanStack Query, MapLibre, Recharts; Python, FastAPI, Pydantic, SQLAlchemy, Pillow, httpx, pytest; PostgreSQL/PostGIS and optional Supabase Auth.

**Spec:** ../specs/2026-11-20-invisivel.md

## Global Constraints
- Interface in Brazilian Portuguese; mobile navigation at most five primary destinations.
- Official data are context, never street-level allegations. No invented counts or affected population.
- Missing values remain null. Municipal observations never become neighborhood statistics.
- Public browsing anonymous; authenticated reports/votes, private moderation with role checks.
- A report never publishes automatically; originals and approved versions retained.
- One active vote per user/issue; votes cannot verify resolution.
- Similarity weights 40% geography, 35% text, 15% category, 10% time; review thresholds .65/.85; no automatic merge.
- Simulation hypothetical, deterministic, budget bounded and never mutates issues.
- Photos privately held, decoded/re-encoded without EXIF and reviewed before publication.
- User opted out of questions. Use the provided checkout; no remote push or publication of citizen data without configured hosting.

## Review Focus
- Broken/unavailable upstream API retains valid previous data and exposes stale/error metadata.
- Anonymous access cannot reveal email, pending reports, private images or audit records.
- Cross-municipality links, wrong UF, invalid coordinates and hostile source URLs are rejected.
- Double votes and concurrent moderation preserve consistent counts and version history.
- A fresh install with no Supabase credentials remains testable, without pretending locally registered email is verified.

### Task 1: API foundation, persistence and access
**Files:** apps/api/app/{main,config,db,models,schemas,security}.py; apps/api/tests/test_access.py; pyproject.toml; scripts/dev.mjs.
**Interfaces:** /api/v1/auth/{register,login,logout,me}; SQLAlchemy session, require_user, require_admin.
- [ ] Write failing access/validation tests, run pytest and inspect RED.
- [ ] Implement persistent local auth, opaque server sessions, password hashing, role checks, rate limiting and error handling.
- [ ] Verify pytest, no public email leakage; provide environment configuration and production restrictions.

### Task 2: Territorial ingestion and provenance
**Files:** apps/api/app/territories.py; pipelines/{sync,connectors}.py; data/official; tests/test_territories.py.
**Interfaces:** states, municipalities, neighborhoods, summary, indicators, geometries and source catalog APIs.
- [ ] Write failing tests for UF ownership, missing data, reference metadata and import preservation.
- [ ] Fetch national official IBGE territorial catalog plus pilot indicators and geometries; persist validated data, audit ingestion.
- [ ] Verify real upstream responses and offline cache; no manufactured neighborhood polygons or indicators.

### Task 3: Collaborative issues and moderation
**Files:** apps/api/app/{issues,moderation,uploads,algorithms}.py; tests/test_participation.py; data/demo.json.
**Interfaces:** issue lists/details/reports/sources/updates/votes, reports/check-duplicates, report submission, upload and admin APIs.
- [ ] Write failing end-to-end tests: private pending content, approval, linkage, immutable original, vote replacement/deletion, permissions, image validation.
- [ ] Implement duplicate scoring, moderation actions, versioned snapshots, status history, evidence approval, audited merge/reopen/restore.
- [ ] Verify invariants and security suite. Optional illustrative issues are explicitly marked demo and excluded from real results.

### Task 4: Simulation and analytics
**Files:** apps/api/app/simulations.py; tests/test_algorithms.py.
**Interfaces:** POST/GET simulations; source-backed territory context; separate documented priority model.
- [ ] Write failing tests for normalized similarity, cross-municipality exclusion, exact budget constraints, determinism and non-mutation.
- [ ] Implement explainable unit-cost allocation and scenario comparison with separate assumptions.
- [ ] Verify edge cases: zero/negative budget, no issues, insufficient data.

### Task 5: Responsive citizen application
**Files:** apps/web/src/{app,components,pages,services,styles}; PWA manifest/service worker; web tests.
**Interfaces:** consumes the versioned API, uses cookie credentials and same-origin dev proxy.
- [ ] Implement accessible dashboard, national territory selector, map/list filters, issue dossier, report wizard, login/profile, moderation, source/methodology/privacy pages and simulator.
- [ ] Implement explicit real/demo switch; show unavailable/stale data; private routes never cached by service worker.
- [ ] Verify TypeScript/build and browser flows at desktop/mobile widths, including form errors, offline shell and keyboard access.

### Task 6: Deployment, review and documentation
**Files:** compose.yaml; Dockerfiles; database/migrations; .github/workflows/ci.yml; README.md; docs.
- [ ] Add repeatable one-command local startup and deployment configuration with HTTPS reverse proxy and environment templates.
- [ ] Run pytest, frontend tests/typecheck/build and full browser report→moderate→vote→simulate flow.
- [ ] Request fresh independent review, fix material findings with regression tests.
- [ ] Update README with every actual dependency, startup, accounts, source provenance, tests, production requirements and honest remaining external prerequisites.
