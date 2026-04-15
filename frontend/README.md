# PRD Generator Mk2 (CodeGarden)

This repo turns a plain-language idea into a practical build plan: recommended stack, PRD output, growth review, and optional GitHub bootstrap.

## Why this README was rewritten

The original README was the default Vite template.
This version summarizes what was actually built from:
- the current codebase,
- implementation plans/spec docs,
- merged PRs and commit history.

## Project snapshot

- **Frontend:** React + Vite + HeroUI + Tailwind.
- **Backend:** FastAPI + modular LLM pipeline.
- **Main flow:** Idea -> recommendation -> refine options -> generate PRDs/env/growth check.
- **Persistence:** Local `backend/sessions.json` for saved sessions.
- **Deploy target:** Render (backend + frontend services in `render.yaml`).

## What the plans/specs introduced

### 1) CodeGarden V1 plan (`2026-04-07`)

One-line summary: define the full-stack MVP pipeline and stage-based UI.

- Added recommendation-first workflow.
- Added generate pipeline (normalize -> analyze -> PRD -> growth check).
- Added deterministic `.env` builder.
- Added test-first backend setup.

### 2) HeroUI migration design + plan (`2026-04-10`)

One-line summary: replace custom CSS primitives with HeroUI components and Tailwind utilities without changing core app logic.

- Migrated major frontend components to HeroUI.
- Swapped `main.css` for `globals.css` + Tailwind/HeroUI imports.
- Kept API flow and state machine intact.

## PR/commit history summary (high level)

This is a condensed product evolution from merged work and first-parent commits:

- **Initial foundation:** backend scaffolding, frontend scaffolding, tests, endpoint wiring.
- **LLM pipeline growth:** recommender, normalizer, analyzer, PRD generator, growth checker, env builder.
- **UI evolution:** recommendation panel default entry, quick setup flow, previous sessions view, iteration feedback loop.
- **API quality/fixes:** request shape alignment, API base URL hardening, session idea normalization fixes.
- **GitHub integration:** repo scaffold creation flow and follow-up fixes.
- **Deployment work:** repeated `render.yaml` improvements for split frontend/backend services.
- **Recent merge:** PR #15 (`claude/explore-idea-dataflow-M4Mi5`) merged into current branch.

## Current user flow

1. Enter an idea.
2. Answer Quick Setup questions.
3. Receive a recommended architecture + tradeoffs.
4. Adjust stack choices in card UI.
5. Generate:
   - Main PRD,
   - optional backend/frontend split PRDs,
   - `.env` template,
   - growth check.
6. Optionally create a GitHub repo scaffold from outputs.

## Backend endpoints

- `POST /quick-setup/questions` -> dynamic onboarding questions.
- `POST /recommend` -> recommendation + architecture/deployment advice.
- `POST /generate` -> PRD outputs + env + growth check.
- `GET /sessions/latest` -> last recommendation session.
- `GET /sessions` -> session list.
- `GET /sessions/{session_id}` -> specific session.
- `POST /sessions/{session_id}/iterate` -> regenerate recommendation using feedback.
- `POST /create-repo` -> create GitHub repo with scaffold files.

## Local setup

### Prerequisites

- Python 3.11+
- Node 18+
- npm

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```bash
OPENAI_API_KEY=your_key_here
# Optional for GitHub scaffold endpoint:
GITHUB_TOKEN=your_token_here
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Set API URL if needed (`frontend/.env`):

```bash
VITE_API_URL=http://localhost:8000
```

## Deployment notes

Render blueprint lives in `render.yaml` and defines two services:

- `prd-generator-backend` (Python/FastAPI)
- `prd-generator-frontend` (Node static build + serve)

Frontend points to backend using `VITE_API_URL`.

## Repository structure (practical view)

- `backend/main.py` -> API routes and orchestration.
- `backend/pipeline/` -> recommendation + generation agents/stages.
- `backend/services/` -> GitHub bootstrap client/helpers.
- `backend/tests/` -> backend test coverage.
- `docs/superpowers/` -> plans/specs documenting implementation intent.
- `frontend/src/App.jsx` -> stage flow + API integration.
- `frontend/src/components/` -> UI building blocks.
- `render.yaml` -> deployment blueprint.

## Notes for this private-use project

- This tool is optimized for one user's fast build workflow.
- Simplicity is preferred over edge-case-heavy architecture.
- Recommendations are meant to be practical defaults, not enterprise design overkill.
