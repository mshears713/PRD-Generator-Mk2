# CodeGarden PRD

## Overview

CodeGarden is a private workflow tool that converts a single project idea into a complete, build-ready blueprint. A user submits an idea, receives an intelligent architecture recommendation, edits stack decisions through a card-based UI, and generates a full PRD, `.env` template, and growth review. The tool is optimized for hackathons, personal tools, and AI-assisted builds — biased toward the simplest viable system rather than enterprise complexity.

## Architecture

The system is a fullstack application with a FastAPI backend acting as the decision and generation brain, and a React frontend acting as the control surface. All LLM orchestration, session management, and output generation runs on the backend. The frontend handles recommendation review, stack selection editing, output display, and optional GitHub repository creation. External clients (including a CustomGPT) can call backend endpoints directly, bypassing UI-specific intake steps entirely.

The backend pipeline runs in two phases: a `/recommend` phase that produces an architecture recommendation package, and a `/generate` phase that runs a four-stage LLM pipeline (Normalizer → Analyzer → PRD Generator → Growth Check) plus a deterministic `.env` builder.

## Components

### Recommender
- **Responsibility:** Interprets the user's idea and constraint answers, commits to one recommended tech stack, and produces a full system understanding with rationale, scope boundaries, and phased build plan.
- **Interface:** Called by `POST /recommend`; receives `idea` string and optional `constraints` dict; returns JSON recommendation package.
- **Key logic:** Single `gpt-4o` call with JSON-mode output. Produces `system_understanding`, `system_type`, `core_system_logic`, `key_requirements`, `scope_boundaries`, `phased_plan`, `recommended` (stack dict), `rationale`, and `confidence` (0–1 score).

### Context Advisor
- **Responsibility:** Generates project-specific tradeoff analysis for the three deployment options (Render, AWS, Self-hosted) and selects exactly one as recommended.
- **Interface:** Called in parallel with Option Advisor after Recommender completes; receives `idea`, `constraints`, and `recommended` stack dict.
- **Key logic:** `gpt-4o` call with JSON-mode output. Only the `deployment` array is used in production; the `architecture` section is superseded by Option Advisor output.

### Option Advisor
- **Responsibility:** Evaluates each of the 12 selectable technology options (3 per field × 4 fields) against the specific project and returns a `fit_score`, `relevant` flag, per-option `reason`, `benefits`, and `drawbacks`.
- **Interface:** 12 parallel `gpt-4o-mini` calls via `ThreadPoolExecutor(max_workers=12)`; called immediately after Recommender, in parallel with Context Advisor.
- **Key logic:** `fit_score < 20` maps to `relevant = false`, hiding that option from the UI. Options with `relevant = true` are shown as selectable cards in the frontend.

### Normalizer
- **Responsibility:** First stage of the generate pipeline. Removes vagueness from the raw idea and final stack selections, producing a clean, unambiguous system definition used by all downstream generate agents.
- **Interface:** Called by `POST /generate`; receives `idea` and `selections` dict.
- **Key logic:** `gpt-4o` call producing `system_name`, `purpose`, `core_features`, `user_types`, `constraints`, and `assumptions_removed`.

### Analyzer
- **Responsibility:** Second stage of the generate pipeline. Converts the normalized system definition into a concrete architecture breakdown: components, data flow, dependencies, and risks.
- **Interface:** Receives the Normalizer's output dict; passes `architecture` JSON to the PRD Generator.
- **Key logic:** `gpt-4o` call producing `components` (4–8 items), `data_flow` (3–6 steps), `dependencies`, and `risks`.

### PRD Generator
- **Responsibility:** Third stage of the generate pipeline. Combines normalized definition and architecture analysis into a full PRD markdown document — the primary user-facing deliverable.
- **Interface:** Receives `normalized` and `architecture` JSON; returns a markdown string rendered directly in the UI.
- **Key logic:** `gpt-4o` plain-text call. Output must contain exactly these sections in order: Overview, Architecture, Components, API Usage, Database Design, Test Cases (minimum 6 rows).

### Backend PRD Generator
- **Responsibility:** Optional decomposition stage. Expands the main PRD into a backend-focused implementation PRD with endpoint specifications, data models, integration details, and four fixed implementation phases.
- **Interface:** Called when PRD decomposition is enabled in config; receives `main_prd`, `normalized`, and `architecture`.
- **Key logic:** `gpt-4o` plain-text call producing sections: Purpose, Responsibilities, Architecture, Endpoints, Data/Models, External Integrations, Validation/Error Handling, Testing Strategy, Out of Scope, Implementation Phases.

### Growth Check
- **Responsibility:** Final stage of the generate pipeline. Reviews the completed PRD and stack selections and produces a structured honest evaluation rendered as three expandable cards.
- **Interface:** Receives the PRD markdown string and `selections` dict; returns `{good, warnings, missing}` — each an array of `{title, detail}` objects.
- **Key logic:** `gpt-4o` JSON-mode call. `good` (2–4 items), `warnings` (1–3 items), `missing` (1–3 genuine gaps). Rendered as green/amber/red-bordered cards in the UI.

### Env Builder
- **Responsibility:** Deterministic `.env` file generator. Produces a commented, labelled `.env` string from selected APIs and database choice with no LLM involvement.
- **Interface:** Called after Growth Check in the generate pipeline; receives `apis` list, `api_keys` dict, and `database` string.
- **Key logic:** Static key maps for OpenRouter, Tavily, Postgres, and Firebase. Always includes `OPENAI_API_KEY`. Outputs one `KEY=value` line per required credential.

### GitHub Bootstrap Service
- **Responsibility:** Creates a GitHub repository, commits scaffold files, and returns a kickoff prompt for external coding agents.
- **Interface:** Called by `POST /create-repo`; receives generated PRD, `.env`, and growth check outputs.
- **Key logic:** GitHub API wrapper assembles scaffold file set, names the repo deterministically, and returns a ready-to-use repository URL and kickoff prompt.

### React Frontend
- **Responsibility:** Provides the user control surface — loading sessions, editing architecture choices, triggering generation, displaying outputs, and initiating GitHub repo creation.
- **Interface:** Calls `/recommend`, `/generate`, `/sessions/*`, and `/create-repo` backend endpoints.
- **Key logic:** Manages a page-level stage state machine (idea → recommending → recommendation → generating → output). Renders recommendation cards, deployment option cards, PRD markdown, growth check cards, and `.env` text.

## API Usage

All LLM calls use the OpenAI API. Temperature is `0.3` across all agents unless noted.

| Agent | Model | Format | Notes |
|---|---|---|---|
| Recommender | `gpt-4o` | JSON object | `response_format: {"type": "json_object"}` |
| Context Advisor | `gpt-4o` | JSON object | Only `deployment` array used in production |
| Option Advisor | `gpt-4o-mini` | JSON object | 12 parallel calls |
| Normalizer | `gpt-4o` | JSON object | First generate stage |
| Analyzer | `gpt-4o` | JSON object | Second generate stage |
| PRD Generator | `gpt-4o` | Markdown string | No `response_format` — plain text |
| Backend PRD Generator | `gpt-4o` | Markdown string | Decomposition path only |
| Growth Check | `gpt-4o` | JSON object | Final generate stage |

GitHub API is used by the Bootstrap Service for repository creation and file commits.

## Database Design

No persistent database is required for the core generation pipeline. Session state is persisted server-side via session snapshots to enable recommendation iteration and session history retrieval. Session data is stored as structured JSON keyed by session ID.

Key session fields: `session_id`, `idea`, `constraints`, `recommendation` (full recommender output), `selections` (confirmed stack), `generated_output` (PRD + growth + env), `created_at`, `updated_at`.

Sessions are retrievable via `/sessions/latest`, `/sessions` (list), and `/sessions/{id}`. Sessions support recommendation re-iteration via `/sessions/{id}/iterate`.

## Test Cases

| Test | Input | Expected Output | Type |
|---|---|---|---|
| Recommend with valid idea | `POST /recommend` with idea string | 200 + recommendation JSON with all required fields | integration |
| Recommend with constraints | `POST /recommend` with idea + constraints dict | Stack selection reflects hard constraints (e.g. auth=none → no auth anywhere) | integration |
| Generate full pipeline | `POST /generate` with idea + selections | 200 + `{prd, env, growth_check}` | integration |
| Env builder — Postgres | selections with `database: postgres` | `DATABASE_URL=postgres://...` present in env output | unit |
| Env builder — API key filled | selections with OpenRouter + provided key | `OPENROUTER_API_KEY=<provided>` in env output | unit |
| PRD sections present | PRD Generator output | All six sections present: Overview, Architecture, Components, API Usage, Database Design, Test Cases | unit |
| Growth check shape | Growth Check output | `good`, `warnings`, `missing` each present and non-empty arrays of `{title, detail}` | unit |
| Option advisor relevance | Option Advisor with `fit_score < 20` | `relevant = false` | unit |
| Confidence range | Recommender output | `confidence` is float between 0 and 1 | unit |
| Session persist and retrieve | `POST /recommend` then `GET /sessions/latest` | Returned session matches submitted idea and recommendation | integration |
| GitHub repo creation | `POST /create-repo` with generated outputs | GitHub repo created, URL returned, kickoff prompt present | e2e |
| External client flow | Direct `POST /recommend` with no UI | Valid recommendation response identical to UI path | e2e |
