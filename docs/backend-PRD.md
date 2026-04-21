# CodeGarden Backend PRD

## Purpose

The CodeGarden backend is the decision and generation brain of the system. It owns all LLM orchestration, session management, architecture recommendation, PRD generation, growth review, and GitHub scaffold creation. It exposes a REST API consumed by the React frontend and by external clients (including a CustomGPT) that can call endpoints directly without UI involvement.

## Responsibilities

- Receive raw project ideas and optional constraint answers and return a full architecture recommendation package.
- Run a sequential LLM pipeline (Normalizer → Analyzer → PRD Generator → Growth Check) to produce a complete build blueprint from confirmed stack selections.
- Produce a deterministic `.env` file from selected APIs and database choices.
- Persist and serve session snapshots to support recommendation iteration and session history.
- Optionally decompose the main PRD into a backend-focused implementation PRD.
- Create GitHub repositories with scaffold files and kickoff prompts on demand.
- Serve a dynamic question generator route for constraint intake.

## Architecture

The backend is a FastAPI application. All business logic lives in `pipeline/` modules — each module corresponds to a single agent or deterministic helper in the recommendation or generation pipeline. The LLM abstraction layer (`llm.py`) wraps model calls with consistent logging, retry, and fake-LLM fallback for test environments. Feature flags and runtime toggles (including PRD decomposition behavior) are centralized in `config.py`. GitHub operations are isolated in `services/`.

The recommend flow is parallel: Recommender runs first, then Context Advisor and Option Advisor execute concurrently. The generate flow is sequential: Normalizer → Analyzer → PRD Generator → Growth Check, followed by synchronous env builder execution.

## Endpoints

| Method | Path | Purpose | Input | Output |
|---|---|---|---|---|
| `POST` | `/recommend` | Generate architecture recommendation + save session | `{idea: string, constraints?: dict, answers?: dict}` | Recommendation package (see Data/Models) |
| `POST` | `/generate` | Run generate pipeline + save session | `{idea, scope, backend, frontend, apis, database, api_keys}` | `{main_prd, backend_prd?, frontend_prd?, env, growth_check, prd_quality?, prd}` |
| `GET` | `/sessions/latest` | Retrieve most recent session | — | Session object |
| `GET` | `/sessions` | List session history | — | Array of session summaries |
| `GET` | `/sessions/{id}` | Retrieve a specific session by ID | `id` path param | Session object |
| `POST` | `/sessions/{id}/iterate` | Re-run recommendation on an existing session | `id` path param + optional updated constraints | New recommendation package |
| `POST` | `/create-repo` | Create GitHub repository from generated artifacts | `{main_prd, backend_prd?, frontend_prd?, env?, repo_name?, private?, idea?}` | `{repo_name, repo_url, kickoff_prompt, created_files}` |
| `POST` | `/quick-setup/questions` | Dynamic question generator for constraint intake | `{idea: string}` | `{questions: [...]}` |
| `GET` | `/health` | Service health check | — | `{status: string}` |

All endpoints accept and return JSON. CORS is open for frontend and external client compatibility.

## Data / Models

### RecommendRequest
```
idea: string           # raw user-submitted idea text
constraints?: dict     # optional QuickSetup answers as key-value pairs (default: {})
answers?: dict         # optional structured answers from dynamic question flow
                       #   {fixed_answers: dict, dynamic_answers: dict}
                       #   when present, overrides constraints (mapped via answer_mapper)
```

### RecommendResponse
```
system_understanding: string        # 4-6 sentence system walkthrough
system_type: string                 # short label (CRUD web app | AI assistant | etc.)
core_system_logic: string           # 1-2 sentences describing the core engine
key_requirements: string[]          # 3-6 concrete technical requirements
scope_boundaries: string[]          # 3-5 in/out-of-scope statements
phased_plan: string[]               # 3-phase build plan
recommended: StackSelection         # recommended stack dict
rationale: dict                     # per-field rationale strings
confidence: object                  # {score: int (0–100), reason: string}
constraint_impact: object[]         # [{constraint: string, impact: string}]
assumptions: string[]               # assumptions made when constraints were sparse
deployment: DeploymentOption[]      # 3 deployment options, one recommended=true
architecture: ArchitectureAdvice    # per-option fit scores and advice
api_candidates: ApiCandidateSet     # selected/candidate/rejected API metadata
```

### StackSelection
```
scope: "frontend" | "backend" | "fullstack"
backend: "fastapi" | "node" | "none"
frontend: "react" | "static" | "none"
apis: string[]          # subset of ["openrouter", "tavily"]
database: "postgres" | "firebase" | "none"
```

### GenerateRequest
```
idea: string
scope: string
backend: string
frontend: string
apis: string[]
database: string
api_keys: dict[str, str]   # user-supplied API key values keyed by api id
```

### GenerateResponse
```
main_prd: string         # main PRD markdown document (always present)
backend_prd?: string     # backend-focused PRD markdown (always generated; may be overridden by decomposer)
frontend_prd?: string    # frontend-focused PRD markdown (present only when decomposition is enabled)
env: string              # .env file contents (plain text)
growth_check: object     # {good, warnings, missing, risk_score?, quick_wins?, blockers?, consistency_issues?}
prd_quality?: object     # {passed: bool, warnings: string[], summary: string}
prd: string              # backward-compat alias for main_prd (legacy frontend support)
```

### CreateRepoRequest
```
main_prd: string         # required — main PRD markdown
backend_prd?: string     # optional backend PRD markdown
frontend_prd?: string    # optional frontend PRD markdown
env?: string             # optional .env file contents
repo_name?: string       # optional override for repository name (validated, slugified)
private?: bool           # whether repo is private (default: true)
idea?: string            # optional original idea text (used for repo naming fallback)
```

### CreateRepoResponse
```
repo_name: string        # final repository name created (may differ from requested if conflict resolved)
repo_url: string         # full GitHub URL of the created repository
kickoff_prompt: string   # ready-to-use prompt for a coding agent to start building
created_files: string[]  # list of file paths committed to the repository
```

### Session
```
session_id: string
idea: string
constraints: dict
recommendation: RecommendResponse
selections?: StackSelection
generated_output?: GenerateResponse
created_at: string       # ISO 8601
updated_at: string       # ISO 8601
```

### DeploymentOption
```
name: string             # "Render" | "AWS" | "Self-hosted"
value: string            # "render" | "aws" | "self"
recommended: bool        # exactly one true per response
reason_for_recommendation: string
benefits: string[]
drawbacks: string[]
sponsored: bool
sponsor_info?: object    # present only for sponsored options
```

### OptionAdvice (per option per field)
```
fit_score: int           # 0–100
relevant: bool           # false when fit_score < 20
reason: string           # one-sentence project-specific fit explanation
benefits: string[]       # 2-3 project-specific benefits
drawbacks: string[]      # 1-2 project-specific drawbacks
```

## External Integrations

### OpenAI API
- Used by all seven LLM agents: Recommender, Context Advisor, Option Advisor (×12 parallel), Normalizer, Analyzer, PRD Generator, Growth Check.
- All calls use `temperature=0.3`. JSON-mode agents use `response_format: {"type": "json_object"}`. PRD Generator uses plain text mode.
- `OPENAI_API_KEY` is required in environment.
- The LLM wrapper (`llm.py`) handles retry logic and routes to a fake-LLM responder when `USE_FAKE_LLM=1` or pytest is detected.

### GitHub API
- Used exclusively by the Bootstrap Service (`services/github_bootstrap.py`, `services/github_client.py`).
- Operations: create repository, create/commit scaffold files (PRD, `.env`, README, kickoff prompt).
- `GITHUB_TOKEN` and `GITHUB_USERNAME` are required in environment when the create-repo endpoint is used.
- GitHub integration is optional — the core recommend/generate flow does not depend on it.

## Validation / Error Handling

- All request bodies are validated via Pydantic models. Invalid shapes return `422 Unprocessable Entity` with field-level error detail.
- Missing `OPENAI_API_KEY` at runtime causes `/recommend` and `/generate` to return `500` with `"OPENAI_API_KEY not set"` detail before any LLM call is attempted.
- LLM JSON parse failures fall back to empty-dict defaults for agent outputs to prevent pipeline crashes. Fields missing from agent output are defaulted to empty strings or empty arrays.
- Option Advisor parallel calls use `ThreadPoolExecutor`; individual option failures are caught and excluded from the merged result without failing the full recommendation response.
- GitHub API failures from `/create-repo` return `500` with the upstream error detail surfaced.
- Session not found on `GET /sessions/{id}` returns `404`.

## Testing Strategy

- Unit tests cover each pipeline module in isolation using `unittest.mock` to patch the OpenAI client. Tests assert output shape, required field presence, and type correctness against fixed fake responses.
- Integration tests cover the FastAPI endpoints via `httpx.TestClient`, patching pipeline functions to verify request routing, response shape, and error handling (missing API key, pipeline failure).
- The fake-LLM mode (`USE_FAKE_LLM=1`) provides deterministic responses for CI environments where live LLM calls are not available.
- Test files are co-located in `backend/tests/` and `tests/` (root-level) and run via pytest.
- Coverage targets: all pipeline modules, all endpoints, env builder edge cases (all API/database combinations), GitHub bootstrap file assembly.

## Out of Scope

- Multi-user authentication and authorization — the system is a single-user private tool.
- Persistent storage beyond session snapshots — no relational database or ORM is in the core pipeline.
- Asynchronous job queuing — all pipeline stages run synchronously within the request lifecycle.
- Frontend serving — the backend serves JSON only; the React frontend is deployed and served separately.
- Rate limiting and abuse prevention — not implemented; single-user scope makes this unnecessary.
- Enterprise features (audit logging, team management, SSO) — explicitly out of scope.

## Implementation Phases

### Phase 1 — Backend skeleton and contracts
- Create FastAPI app with CORS middleware and Pydantic request/response models for `/recommend` and `/generate`.
- Implement `GET /health` returning `{status: "ok"}`.
- Implement `llm.py` wrapper with fake-LLM fallback for test environments.
- Verify: `POST /recommend` with mocked pipeline returns 200 with correct response shape; `POST /generate` same.

### Phase 2 — Core request flow and business logic
- Implement Recommender, Context Advisor, and Option Advisor pipeline modules with their system prompts.
- Wire parallel execution of Context Advisor + Option Advisor after Recommender in `/recommend`.
- Implement Normalizer, Analyzer, PRD Generator, and Growth Check pipeline modules.
- Wire sequential generate pipeline in `/generate`; add Env Builder as deterministic final step.
- Verify: End-to-end `/recommend` → `/generate` flow with live or fake LLM returns valid PRD markdown, `.env` string, and growth check object.

### Phase 3 — External integrations and data handling
- Implement session persistence: save session after `/recommend`; update after `/generate`; expose `/sessions/latest`, `/sessions`, `/sessions/{id}`, `/sessions/{id}/iterate`.
- Implement GitHub client and bootstrap service; wire `/create-repo` endpoint.
- Implement `api_registry.py` and API candidate selector; wire into Recommender output.
- Add `POST /quick-setup/questions` dynamic question generator route (body: `{idea: string}`, response: `{questions: [...]}`).  
- Verify: Session retrieved after recommendation matches submitted idea; `/create-repo` returns repo URL and kickoff prompt against GitHub API (or mock).

### Phase 4 — Validation, tests, and polish
- Write unit tests for all pipeline modules (Recommender, Context Advisor, Option Advisor, Normalizer, Analyzer, PRD Generator, Growth Check, Env Builder).
- Write integration tests for all endpoints using `TestClient` with mocked pipeline functions.
- Add missing-API-key guard to `/recommend` and `/generate` with `500` response.
- Enable optional PRD decomposition via `config.py` flag; integrate Backend PRD Generator into generate pipeline when enabled.
- Verify: All tests pass; fake-LLM mode produces deterministic output; decomposition flag toggles backend PRD inclusion in generate response.
