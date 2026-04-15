# PRD-Generator-Mk2 (StackLens / CodeGarden)

A private workflow tool that turns one project idea into:
- a recommended architecture,
- editable stack decisions,
- PRD output (main + optional backend/frontend split),
- a generated `.env` template,
- a growth/system review,
- and an optional GitHub repository scaffold.

## What this project is now (current direction)

This project is now **API-first + output-focused**, not an onboarding-heavy app.

- The core input is a single idea sent to the backend (often from an external client such as a CustomGPT).
- The frontend is mainly used for **reviewing/editing architecture choices**, **generating PRDs**, and **sending outputs to GitHub**.
- Quick setup question infrastructure still exists in the codebase, but current behavior is centered on recommendation/edit/generate/repo flow.

## End-to-end workflow (descriptive)

1. **Idea intake**
   - An idea is submitted to `POST /recommend` (directly or through UI wiring).

2. **Recommendation pass**
   - Backend builds a system recommendation (scope/backend/frontend/APIs/database).
   - Backend also returns rationale, architecture option scoring, deployment options, confidence, and API candidate analysis.
   - The recommendation is stored as a session snapshot for later reuse/iteration.

3. **Recommendation editing**
   - Frontend shows selectable cards for architecture choices.
   - You can keep defaults or override any field before generation.
   - Optional feedback iteration can regenerate recommendations for the same session.

4. **Generation pass**
   - Edited selections are sent to `POST /generate`.
   - Backend runs normalization -> architecture analysis -> PRD generation -> growth check.
   - If decomposition is enabled, backend splits a main PRD into backend/frontend PRDs.
   - Backend also produces a deterministic `.env` output from selected APIs/database.

5. **Output handling**
   - Frontend displays growth review, PRD documents, and `.env` text.
   - Outputs can be copied/downloaded.

6. **GitHub scaffold (optional)**
   - Frontend calls `POST /create-repo` with generated outputs.
   - Backend creates a repo, commits scaffold files, and returns a kickoff prompt.

## Runtime architecture

### Backend role

The backend is the project brain and contract owner.

- Owns all decision/generation orchestration.
- Persists and normalizes sessions.
- Provides recommendation, iteration, generation, and repo-bootstrap APIs.
- Houses LLM prompt logic and deterministic helpers (env builder, repo naming, file scaffolding).

### Frontend role

The frontend is the project control surface.

- Loads latest/previous sessions.
- Shows recommendation summary + editable options.
- Sends final selections to generate outputs.
- Displays PRDs/growth/env.
- Triggers GitHub repo creation.

### External-client role

External clients (including a CustomGPT) can call backend endpoints directly and bypass UI-specific intake steps.

## Key API surface (conceptual)

- `/recommend`: produce recommendation package + save session.
- `/generate`: produce PRD package + growth check + `.env`.
- `/sessions/*`: load latest, list history, fetch one, iterate recommendation.
- `/create-repo`: create GitHub repository scaffold from generated artifacts.
- `/quick-setup/questions`: dynamic question generator route kept in codebase.

## Repository map (one-line descriptions)

### Root-level

- `README.md` — full project-level description (this file).
- `render.yaml` — Render blueprint for backend + frontend services.
- `AGENTS_Defined.md` — main agent prompt/reference document.
- `AGENTS_Defined_delta1.md` — follow-on tuning/addendum for agent behavior.
- `docs/superpowers/` — planning/spec docs made for agent-assisted implementation.

### Backend

- `backend/main.py` — FastAPI app, request/response contracts, endpoint orchestration.
- `backend/config.py` — feature flags and runtime toggles (including PRD decomposition behavior).
- `backend/llm.py` — model call wrapper used by pipeline modules.
- `backend/pipeline/recommender.py` — primary architecture recommendation logic.
- `backend/pipeline/context_advisor.py` — deployment/context tradeoff generation.
- `backend/pipeline/option_advisor.py` — per-option fit/benefit/drawback scoring.
- `backend/pipeline/api_candidate_selector.py` — API candidate filtering/ranking.
- `backend/pipeline/normalizer.py` — converts idea+selections into structured system definition.
- `backend/pipeline/analyzer.py` — architecture/dataflow analysis stage.
- `backend/pipeline/prd_gen.py` — main PRD generation stage.
- `backend/pipeline/prd_decomposer.py` — optional split into backend/frontend PRDs.
- `backend/pipeline/backend_prd_gen.py` — backend-focused PRD writer helper.
- `backend/pipeline/frontend_prd_gen.py` — frontend-focused PRD writer helper.
- `backend/pipeline/growth.py` — growth/system review generation.
- `backend/pipeline/env_builder.py` — deterministic `.env` builder.
- `backend/pipeline/question_generator.py` — dynamic question templates and selection logic.
- `backend/pipeline/answer_mapper.py` — maps answered questions into constraints/derived context.
- `backend/pipeline/prd_contract.py` — output/structure contract helpers.
- `backend/services/github_client.py` — GitHub API wrapper.
- `backend/services/github_bootstrap.py` — scaffold file assembly, naming, kickoff prompt creation.
- `backend/data/api_registry.json` + `api_registry.py` — API metadata used in recommendation context.
- `backend/tests/` — backend unit/integration coverage across pipeline and services.

### Frontend

- `frontend/src/App.jsx` — page-level state machine and API wiring.
- `frontend/src/components/RecommendationPanel.jsx` — editable architecture/deployment choices and iterate control.
- `frontend/src/components/SelectionCards.jsx` — stack selection card groups.
- `frontend/src/components/DeploymentRow.jsx` — deployment option selection row.
- `frontend/src/components/OutputPanel.jsx` — PRD tabs, growth cards, `.env`, and GitHub create-repo UI.
- `frontend/src/components/QuickSetupPanel.jsx` — dynamic/fixed question UI path still present in code.
- `frontend/src/data/options.js` — frontend option metadata.
- `frontend/src/data/quickSetup.js` — quick setup question definitions.
- `frontend/src/styles/globals.css` — global Tailwind/HeroUI + markdown styles.
- `frontend/src/components/__tests__/` + `frontend/src/data/__tests__/` — frontend behavioral tests.

## "Superpowers" and agent-oriented files (important context)

Several files were created for Claude/Codex-driven implementation workflows.

- `docs/superpowers/plans/*` are execution plans for agent task sequencing.
- `docs/superpowers/specs/*` are design docs used to guide migrations (e.g., HeroUI move).
- `AGENTS_Defined*.md` files describe prompt policy/tuning for recommendation quality.

These files are **project memory and implementation guidance**, not direct runtime dependencies.

## Change trajectory (from commits + PRs)

High-level evolution of the repository:

- Started as a staged full-stack PRD generator with test-first backend pipeline work.
- Added recommendation intelligence, option scoring, growth checks, and contract hardening.
- Added PRD decomposition and GitHub scaffold creation.
- Migrated frontend UI primitives to HeroUI/Tailwind.
- Shifted UX toward recommendation/edit/generate and persisted sessions.
- Hardened deployment and API routing via repeated `render.yaml` and request-shape fixes.
- Latest merged branch in history: PR #15 (`claude/explore-idea-dataflow-M4Mi5`).

## Practical stance for this private project

- Single-user productivity is prioritized over enterprise complexity.
- Simplicity and fast iteration are preferred over edge-case-heavy architecture.
- The tool is meant to produce actionable build direction quickly, then hand off execution to coding tools.
