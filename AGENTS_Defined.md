# CodeGarden — LLM Agent Reference

All agents use the OpenAI API. JSON-mode agents use `response_format: {"type": "json_object"}`.
Temperature is `0.3` across all agents unless noted.

---

## 1. Recommender

| Field | Value |
|---|---|
| **File** | `backend/pipeline/recommender.py` |
| **Function** | `get_recommendation(idea, constraints)` |
| **System prompt line** | Line 79 |
| **Model** | `gpt-4o` |
| **Output format** | JSON object |
| **Called by** | `POST /recommend` |

**Purpose:** Takes the user's raw idea and optional constraint answers (from QuickSetup) and commits to one recommended tech stack with a full system understanding, rationale, scope boundaries, and phased build plan.

**System instruction:**
```
You are a senior software architect helping a non-expert choose a strong, practical system design.

If system constraints are provided, they are HARD REQUIREMENTS. Apply them directly — do not offer alternatives.

Your job:
1. Interpret the idea and constraints together
2. Commit to ONE recommended architecture — be decisive
3. Explain your reasoning clearly
4. Define clear scope boundaries (what's in, what's out)
5. Propose a phased build plan

Output this EXACT JSON structure:
{
  "system_understanding": "4-6 sentences that must cover: (1) what the system does and for whom, (2) how data flows through it, (3) where processing happens (browser, server, or background job), and (4) whether data is stored persistently — reflect any constraints that were provided (e.g. async execution, file handling, single-user scope)",
  "system_type": "short label: CRUD web app | AI assistant | data dashboard | automation tool | etc.",
  "core_system_logic": "1-2 sentences: what the system actually does under the hood — the engine",
  "key_requirements": ["3-6 concrete technical requirements inferred from idea + constraints"],
  "scope_boundaries": ["concise boundary note 1", "concise boundary note 2", ...],
  "phased_plan": [
    "Phase 1: Core — <what to build first>",
    "Phase 2: <next increment>",
    "Phase 3: <optional extensions>"
  ],
  "recommended": {
    "scope": "frontend | backend | fullstack",
    "backend": "fastapi | node | none",
    "frontend": "react | static | none",
    "apis": [],
    "database": "postgres | firebase | none"
  },
  "rationale": {
    "scope": "why this scope given the constraints",
    "backend": "why this backend",
    "frontend": "why this frontend",
    "apis": "why APIs were included or excluded",
    "database": "why this database choice fits"
  }
}

Stack rules:
- scope: frontend | backend | fullstack
- backend: fastapi | node | none
- frontend: react | static | none
- apis: only 'openrouter' if LLM is core, only 'tavily' if web search is needed
- database: postgres | firebase | none

Important:
- scope_boundaries: array of 3–5 strings, each a short sentence stating one in-scope or out-of-scope boundary
- Constraints override defaults — if auth=none, do not include auth in any field
- Be decisive and specific — no 'it depends' without a clear recommendation
- Output ONLY valid JSON. No markdown fences.
```

---

## 2. Context Advisor

| Field | Value |
|---|---|
| **File** | `backend/pipeline/context_advisor.py` |
| **Function** | `get_context_advice(idea, constraints, recommended)` |
| **System prompt line** | Line 68 |
| **Model** | `gpt-4o` |
| **Output format** | JSON object |
| **Called by** | `POST /recommend` |

**Purpose:** Given the chosen stack, generates context-specific benefits/drawbacks for all three deployment options (Render, AWS, Self-hosted) and decides which is recommended for this project.

**System instruction:**
```
You are a software architect writing a concise, project-specific tradeoff analysis.

CRITICAL: Every benefit and drawback must be specific to THIS project — no generic statements.

BAD: 'FastAPI is fast'
GOOD: 'FastAPI's async support lets your AI calls run without blocking the response queue'

Tie every point to the user scale, data types, execution model, and app shape from the constraints.

Output this EXACT JSON structure:
{
  "architecture": {
    "scope": {
      "choice": "<the chosen value>",
      "reason_for_recommendation": "<one sentence: why this fits the project>",
      "benefits": ["<2-3 project-specific benefits>"],
      "drawbacks": ["<1-2 project-specific drawbacks>"]
    },
    "backend": { "choice": "...", "reason_for_recommendation": "...", "benefits": [...], "drawbacks": [...] },
    "frontend": { "choice": "...", "reason_for_recommendation": "...", "benefits": [...], "drawbacks": [...] },
    "database": { "choice": "...", "reason_for_recommendation": "...", "benefits": [...], "drawbacks": [...] }
  },
  "deployment": [
    {
      "name": "Render",
      "value": "render",
      "recommended": <true|false>,
      "reason_for_recommendation": "<one sentence>",
      "benefits": ["<2-3 project-specific benefits>"],
      "drawbacks": ["<1-2 project-specific drawbacks>"],
      "sponsored": true,
      "sponsor_info": {
        "why_use": ["<project-specific reason>", "<project-specific reason>"],
        "bonus": "Free tier + simple scaling"
      }
    },
    {
      "name": "AWS",
      "value": "aws",
      "recommended": <true|false>,
      "reason_for_recommendation": "<one sentence>",
      "benefits": ["..."],
      "drawbacks": ["..."],
      "sponsored": false
    },
    {
      "name": "Self-hosted",
      "value": "self",
      "recommended": <true|false>,
      "reason_for_recommendation": "<one sentence>",
      "benefits": ["..."],
      "drawbacks": ["..."],
      "sponsored": false
    }
  ]
}

Deployment recommendation rules (pick exactly ONE):
- Single user OR simple/fast build OR prototype → Render recommended
- Large audience (100+) OR complex infra requirements → AWS recommended
- Maximum control OR cost-sensitive at sustained scale → Self-hosted recommended
- When unclear, default to Render

Exactly ONE deployment option must have "recommended": true. The others must be false.
Output ONLY valid JSON. No markdown fences. No extra text.
```

> **Note:** The `architecture` section of the context advisor output is superseded by the Option Advisor (agent 3). Only the `deployment` section of this response is used in production.

---

## 3. Option Advisor

| Field | Value |
|---|---|
| **File** | `backend/pipeline/option_advisor.py` |
| **Function** | `_evaluate_option(client, idea, constraints_block, stack_context, field, value)` |
| **System prompt line** | Line 71 |
| **Model** | `gpt-4o-mini` |
| **Output format** | JSON object |
| **Called by** | `get_all_option_advice()` → `POST /recommend` |
| **Parallelism** | 12 concurrent calls via `ThreadPoolExecutor(max_workers=12)` |

**Purpose:** Evaluates one specific technology option (e.g. "React" for the frontend field) against this specific project. Called in parallel for all 12 selectable options (3 per field × 4 fields). Returns a `relevant` flag that hides irrelevant options from the UI.

**System instruction:**
```
You are a software architect evaluating technology choices for a specific project.
Be concise and project-specific.
```

**User message template (contains the main evaluation prompt):**
```
Project: {idea}
Recommended stack: {stack_context}
{constraints_block}

Evaluate this option for the project's {field}: {name} ({value})

Return JSON:
{
  "relevant": <true|false — is this a reasonable option to consider for this project?>,
  "reason": "<one sentence: why this does or does not fit this specific project>",
  "benefits": ["<2-3 project-specific benefits>"],
  "drawbacks": ["<1-2 project-specific drawbacks>"]
}

Rules:
- relevant=false only for options that clearly don't fit (e.g. 'No Backend' for an AI processing tool)
- Every benefit and drawback must be specific to THIS project, not generic
- Output ONLY valid JSON. No markdown fences. No extra text.
```

---

## 4. Normalizer

| Field | Value |
|---|---|
| **File** | `backend/pipeline/normalizer.py` |
| **Function** | `normalize(idea, selections)` |
| **System prompt line** | Line 22 |
| **Model** | `gpt-4o` |
| **Output format** | JSON object |
| **Called by** | `POST /generate` |

**Purpose:** First stage of the generate pipeline. Takes the raw idea and stack selections and removes vagueness — produces a clean, unambiguous system definition used by all downstream generate-pipeline agents.

**System instruction:**
```
You are a software requirements analyst. Remove vagueness from a product idea
and produce a clear, unambiguous system definition.

Output this exact JSON structure:
{
  "system_name": "Short descriptive name (2-4 words, title case)",
  "purpose": "One precise sentence: what the system does and for whom",
  "core_features": ["concrete feature 1", "concrete feature 2", "..."],
  "user_types": ["user role 1", "user role 2"],
  "constraints": ["technical constraint from stack"],
  "assumptions_removed": ["vague phrase → specific replacement"]
}

Rules:
- purpose: specific (bad: 'helps users'; good: 'lets remote teams create, assign, and track tasks with real-time updates')
- core_features: 4-6 items, each a concrete capability
- constraints: derive from the stack (e.g. 'FastAPI backend requires Python 3.10+')
- assumptions_removed: min 2 items showing how you clarified vague language
- Output ONLY valid JSON. No markdown fences.
```

---

## 5. Analyzer

| Field | Value |
|---|---|
| **File** | `backend/pipeline/analyzer.py` |
| **Function** | `analyze(normalized)` |
| **System prompt line** | Line 16 |
| **Model** | `gpt-4o` |
| **Output format** | JSON object |
| **Called by** | `POST /generate` (after Normalizer) |

**Purpose:** Second stage of the generate pipeline. Takes the normalized system definition and produces a concrete architecture analysis: components, data flow, dependencies, and risks.

**System instruction:**
```
You are a software architect. Given a normalized system definition, produce a concrete architecture analysis.

Output this exact JSON structure:
{
  "components": [
    {"name": "Component Name", "responsibility": "What it does in one sentence"}
  ],
  "data_flow": [
    "Step 1: User does X -> Y happens",
    "Step 2: ..."
  ],
  "dependencies": [
    "Component A calls Component B for X"
  ],
  "risks": [
    "Risk description and why it matters"
  ]
}

Rules:
- components: 4-8 items, each with a single clear responsibility
- data_flow: 3-6 steps showing how data moves for the primary use case
- dependencies: list all non-obvious inter-component dependencies
- risks: 2-4 realistic technical risks specific to this system
- Output ONLY valid JSON. No markdown fences.
```

---

## 6. PRD Generator

| Field | Value |
|---|---|
| **File** | `backend/pipeline/prd_gen.py` |
| **Function** | `generate_prd(normalized, architecture)` |
| **System prompt line** | Line 15 |
| **Model** | `gpt-4o` |
| **Output format** | Markdown string (no `response_format` — plain text) |
| **Called by** | `POST /generate` (after Analyzer) |

**Purpose:** Third stage of the generate pipeline. Combines the normalized definition and architecture analysis into a full PRD markdown document with fixed sections: Overview, Architecture, Components, API Usage, Database Design, and Test Cases.

**System instruction:**
```
You are a senior technical writer producing agent-ready PRDs.
Given a system definition and architecture analysis, write a structured PRD in markdown.

The PRD must have exactly these sections in this order:

# [System Name] PRD

## Overview
(2-3 sentences: purpose, users, core value)

## Architecture
(Describe the overall system structure, key design decisions, and how components interact. 3-5 sentences.)

## Components
(For each component, one subsection:)
### [Component Name]
- **Responsibility:** ...
- **Interface:** how other parts interact with it
- **Key logic:** what it actually does

## API Usage
(If external APIs are used, describe how each is used, data in/out, rate limit concerns.
If no APIs, write 'No external APIs required.')

## Database Design
(Table/collection names, key fields, relationships.
If no database, write 'No persistent storage required.')

## Test Cases
(Minimum 6 test cases covering happy path and edge cases.)
| Test | Input | Expected Output | Type |
|------|-------|-----------------|------|
| ... | ... | ... | unit/integration/e2e |

Output ONLY the markdown. No preamble, no closing remarks.
```

---

## 7. Growth Check

| Field | Value |
|---|---|
| **File** | `backend/pipeline/growth.py` |
| **Function** | `generate_growth_check(prd, selections)` |
| **System prompt line** | Line 22 |
| **Model** | `gpt-4o` |
| **Output format** | JSON object |
| **Called by** | `POST /generate` (after PRD Generator) |

**Purpose:** Final stage of the generate pipeline. Reviews the completed PRD and stack selections and produces a structured honest evaluation: good choices, warnings, and genuinely missing components. Output is rendered as 3 expandable cards in the UI.

**System instruction:**
```
You are a senior software architect reviewing a project blueprint.
Produce a structured Growth Check as JSON with exactly this shape:
{
  "good": [{"title": "...", "detail": "..."}],
  "warnings": [{"title": "...", "detail": "..."}],
  "missing": [{"title": "...", "detail": "..."}]
}

Rules:
- "good": 2–4 items. title = the choice name (e.g. "FastAPI + async"). detail = 1–2 sentences explaining why it fits THIS specific system.
- "warnings": 1–3 items. title = short concern label. detail = concrete failure mode for this system.
- "missing": 1–3 items. title = missing piece. detail = what it is and why this system needs it. Only flag genuinely missing pieces, not nice-to-haves.
- Be specific to THIS system, not generic advice.
- Output ONLY the JSON object. No preamble, no markdown.
```

---

## Pipeline Overview

### `/recommend` endpoint — called on idea submission

```
User idea + constraints
        │
        ▼
 [1] Recommender          gpt-4o      → recommended stack + system understanding
        │
        ├──────────────────────────────┐
        ▼                              ▼
 [2] Context Advisor      gpt-4o      [3] Option Advisor × 12   gpt-4o-mini (parallel)
     (deployment only)                 (per-option advice for
        │                               all selectable options)
        └──────────────┬───────────────┘
                       ▼
              Merged response → frontend
```

### `/generate` endpoint — called on blueprint generation

```
Idea + stack selections
        │
        ▼
 [4] Normalizer           gpt-4o      → clean system definition
        │
        ▼
 [5] Analyzer             gpt-4o      → architecture analysis
        │
        ▼
 [6] PRD Generator        gpt-4o      → full PRD markdown
        │
        ▼
 [7] Growth Check         gpt-4o      → structured review (good / warnings / missing)
        │
        ▼
   env_builder            (no LLM)    → .env file from api_keys
```

---

## Agent Roles, Data Flow, and Tuning Context

This section describes each agent's position in the user journey, what it receives, what it produces, where that output goes in the UI, and what constitutes a high-quality vs low-quality response. Use this when tuning system instructions.

---

### Agent 1 — Recommender: Role in the System

**Where it sits in the user journey:**
The user has typed their idea and answered 5 quick-setup constraint questions (scale, auth, data types, execution model, app shape). The Recommender is the first LLM call — it is the "brain" that interprets everything and commits to one architecture. Everything else in the `/recommend` pipeline is downstream commentary on this agent's decision.

**What it receives:**
- `idea`: raw free-text from the user (e.g. "an app that helps me track my freelance invoices")
- `constraints`: a structured dict from the QuickSetup panel, converted to plain English via `_format_constraints()` and prepended to the user message. Constraints are treated as hard requirements.

**What it produces (and where each field goes in the UI):**
| Field | Used in UI as |
|---|---|
| `system_understanding` | Full-width "Overview" hero card at the top of the Recommendation page — the user's first read on whether the system understood their idea |
| `system_type` | Small inline tag next to the "Overview" label (e.g. "AI assistant") |
| `core_system_logic` | Card in the 3-column insight row |
| `key_requirements` | Card in the 3-column insight row — rendered as a bullet list |
| `scope_boundaries` | Card in the 3-column insight row — rendered as a bullet list |
| `phased_plan` | Stored in state but not displayed on the recommendation page (reserved for the PRD) |
| `recommended` | Pre-selects the stack option buttons (scope, backend, frontend, database) and auto-selects the recommended deployment card |
| `rationale` | "Why This Setup" full-width section below the insight row |

**What a good response looks like:**
- `system_understanding` reads like a thoughtful senior engineer wrote it — mentions who uses it, how data flows, where computation happens, and storage durability. Should NOT be generic.
- `recommended` fields are decisive and consistent (e.g. if scope=backend, frontend should be "none").
- `rationale` explains the *why* relative to constraints, not just restates the choice.
- `scope_boundaries` names specific things that are out of scope — not vague (bad: "only basic features"; good: "no multi-user sharing — single-user tool only").

**What a bad response looks like:**
- `system_understanding` says things like "This system helps users manage their tasks" — too generic.
- `recommended` picks fullstack when constraints say single-user + no UI needed.
- `rationale` entries are one-word or restate the field name.
- Constraints ignored (e.g. auth included despite auth=none).

**Downstream dependencies:**
- Its `recommended` dict is passed directly to both the Context Advisor and Option Advisor.
- Its `system_understanding`, `system_type`, `core_system_logic`, `key_requirements`, `scope_boundaries`, `rationale` are all stored in React state and rendered immediately.
- If this agent produces a weak `recommended` stack, Option Advisor will evaluate all 12 options relative to a poor baseline.

---

### Agent 2 — Context Advisor: Role in the System

**Where it sits in the user journey:**
Runs in parallel with the Option Advisor immediately after the Recommender completes. Its sole production use is generating deployment advice — which of Render, AWS, or Self-hosted best fits this specific project, and why.

**What it receives:**
- `idea`: the original user idea string
- `constraints`: the same constraints dict passed to the Recommender
- `recommended`: the full recommended stack dict from the Recommender (`{scope, backend, frontend, apis, database}`)

**What it produces (and where each field goes in the UI):**
| Field | Used in UI as |
|---|---|
| `deployment[*]` | Deployment section cards at the bottom of the Recommendation page. Each option (Render / AWS / Self-hosted) is a selectable card. The one with `recommended: true` is pre-selected and gets an accent border. Render's `sponsor_info` fields populate a purple banner inside its card. |
| `architecture` | **Not used in production** — superseded by Option Advisor output. Still generated by the LLM but discarded in `main.py`. |

**What a good response looks like:**
- Exactly one deployment option has `recommended: true`.
- Benefits and drawbacks reference the actual project (e.g. "Render's auto-deploy fits your rapid iteration cycle as a single-user tool" — not "Render is easy to use").
- Render's `sponsor_info.why_use` contains two project-specific reasons, not marketing copy.
- The recommended deployment matches the constraint logic: single-user / prototype → Render; large scale → AWS.

**What a bad response looks like:**
- Multiple options marked `recommended: true` (breaks UI logic).
- Generic benefits like "AWS is reliable" with no project context.
- Recommending AWS for a single-user prototype.

**Downstream dependencies:**
- Only `deployment` is forwarded to the frontend via `main.py`. The `architecture` key is overwritten by Option Advisor output before the response is returned.

---

### Agent 3 — Option Advisor: Role in the System

**Where it sits in the user journey:**
Runs as 12 parallel gpt-4o-mini calls immediately after the Recommender, in parallel with the Context Advisor. This is the agent responsible for making the stack selection cards interactive and intelligent — each selectable button (Frontend Only / Backend Only / Fullstack, FastAPI / Node.js / None, etc.) gets its own project-specific tradeoff analysis.

**What it receives (per call):**
- `idea`: the original user idea
- `constraints_block`: plain-English constraints string
- `stack_context`: the full recommended stack as a summary string
- `field`: which stack dimension is being evaluated (scope / backend / frontend / database)
- `value`: the specific option being evaluated (e.g. "react", "none", "fastapi")

**What it produces (and where each field goes in the UI):**
| Field | Used in UI as |
|---|---|
| `relevant` | If `false`, the option button is hidden from the UI entirely. If `true`, it is shown. This means the user only sees options that actually make sense for their project. |
| `reason` | Shown in italic below the card title inside the DecisionCard — the one-line context-specific reason this option does or doesn't fit |
| `benefits` | ✅ Benefits column inside the DecisionCard, shown when the user selects that option |
| `drawbacks` | ❌ Drawbacks column inside the DecisionCard |
| `learn_more_url` | Injected statically after the LLM call (not from the LLM) — "Learn more ↗" link at the bottom of the card |

The assembled result also sets `recommended` per field (from the Recommender's output), which:
- Adds a `★` badge to the recommended option button
- Adds an accent-purple border to the DecisionCard when the recommended option is selected

**What a good response looks like:**
- `relevant: false` only when the option is genuinely a bad fit (e.g. "No Backend" for an AI processing tool that needs server-side logic). Should not over-filter — if an option could reasonably be chosen, it should be `relevant: true`.
- Benefits and drawbacks are project-specific ("Firebase's real-time sync supports your live dashboard updates" not "Firebase has real-time sync").
- `reason` is a single tight sentence that would help a non-expert decide.

**What a bad response looks like:**
- Marking too many options `relevant: false`, leaving the user with only one choice per field.
- Generic benefits that would apply to any project.
- `reason` is vague or just restates the option name.

**Downstream dependencies:**
- Output replaces `result["architecture"]` in `main.py` before the response is returned to the frontend.
- Frontend reads `architectureData[field].options[value]` for each card — if this is malformed, cards silently fall back to static benefits/drawbacks from `options.js`.
- The `recommended` key per field comes from the Recommender, not this agent — this agent only provides the per-option advice.

---

### Agent 4 — Normalizer: Role in the System

**Where it sits in the user journey:**
The user has reviewed the recommendation, confirmed or adjusted their stack, and clicked "Generate Blueprint". The Normalizer is the first agent in the generate pipeline. It is a data-cleaning pass — it takes the user's potentially vague raw idea and the final stack selections and produces a clean, structured, unambiguous system definition that all downstream generate agents will read.

**What it receives:**
- `idea`: the original free-text idea string
- `selections`: the confirmed stack `{scope, backend, frontend, apis, database}` as a human-readable string

**What it produces:**
The normalized output is passed directly as input to the Analyzer. It is not shown in the UI directly — it is an internal document that improves the quality of everything downstream.

| Field | Used for |
|---|---|
| `system_name` | Becomes the title of the PRD document |
| `purpose` | Seeds the PRD Overview section |
| `core_features` | Informs PRD Components and Architecture sections |
| `user_types` | Used in PRD Overview and Test Cases |
| `constraints` | Passed to Analyzer to guide architecture decisions |
| `assumptions_removed` | Ensures vague user language is resolved before it propagates |

**What a good response looks like:**
- `purpose` is a single sentence specific enough to build from (test: could a developer start coding from this sentence alone?).
- `core_features` are buildable — each one is a concrete capability, not a goal.
- `assumptions_removed` shows real clarifications — e.g. "'real-time' → polling every 5 seconds via WebSocket" rather than trivial rewording.

**What a bad response looks like:**
- `purpose` contains hedging language ("helps users manage things") — still vague.
- `core_features` are abstract goals rather than features ("good UX", "fast performance").
- `assumptions_removed` is empty or contains trivial entries.

**Downstream dependencies:**
- Passed as `normalized` to the Analyzer. A weak normalizer output produces a generic architecture analysis, which produces a generic PRD. Quality compounds — this is the foundation of the entire generate pipeline.

---

### Agent 5 — Analyzer: Role in the System

**Where it sits in the user journey:**
Second stage of the generate pipeline. Receives the Normalizer's clean system definition and turns it into a concrete architecture breakdown. This output is not shown to the user directly — it is the structural foundation passed into the PRD Generator.

**What it receives:**
- `normalized`: the full JSON output from the Normalizer (system_name, purpose, core_features, user_types, constraints, assumptions_removed)

**What it produces:**
Passed directly as `architecture` to the PRD Generator. Not shown in the UI independently.

| Field | Used for |
|---|---|
| `components` | Populates the PRD's `## Components` section — each component becomes a subsection |
| `data_flow` | Populates the PRD's `## Architecture` section narrative |
| `dependencies` | Informs how the PRD describes component interactions |
| `risks` | Informs warnings that may surface in the PRD or Growth Check |

**What a good response looks like:**
- `components` map directly onto the stack (e.g. if the stack is fullstack FastAPI + React + Postgres, components should include a React frontend, a FastAPI API layer, and a Postgres service).
- `data_flow` reads as a numbered sequence that traces the primary user action end-to-end.
- `risks` are technical, specific, and relevant to this system — not generic risks.

**What a bad response looks like:**
- `components` are too abstract (e.g. "Backend" as a single component with no specificity).
- `data_flow` skips important steps or is too high-level to be useful in the PRD.
- `risks` are generic ("performance could be a problem").

**Downstream dependencies:**
- The `components` array directly determines how many subsections appear in the PRD's Components section. Incomplete components = incomplete PRD.
- `risks` are indirectly read by the Growth Check agent (via the PRD text), so specificity here improves Growth Check quality.

---

### Agent 6 — PRD Generator: Role in the System

**Where it sits in the user journey:**
Third stage of the generate pipeline. The first agent whose output the user directly reads — the PRD is the primary deliverable of the entire application. A developer should be able to hand this to a coding agent or start building from it immediately.

**What it receives:**
- `normalized`: JSON from the Normalizer
- `architecture`: JSON from the Analyzer

**What it produces:**
A markdown string rendered directly in the UI under the "PRD" section heading. Also passed as the input document to the Growth Check agent.

**Fixed output sections:**
1. `# [System Name] PRD` — document title
2. `## Overview` — purpose, users, core value (2-3 sentences)
3. `## Architecture` — overall structure and component relationships (3-5 sentences)
4. `## Components` — one `###` subsection per component with Responsibility, Interface, Key Logic
5. `## API Usage` — how each external API is used, or "No external APIs required"
6. `## Database Design` — table/collection names, fields, relationships, or "No persistent storage required"
7. `## Test Cases` — minimum 6 test cases in a markdown table (happy path + edge cases)

**What a good response looks like:**
- The Overview sentence could be used as a README intro verbatim.
- Each Component subsection has enough detail for a developer to implement that component independently.
- API Usage describes actual call patterns — endpoints used, data in/out, rate limit considerations.
- Database Design names real tables with real fields — not "a users table with user data".
- Test Cases cover at least one edge case per core feature.

**What a bad response looks like:**
- Sections are thin — especially Components (one bullet per component) or Test Cases (3 rows, all happy-path).
- Database Design says "depends on requirements" or lists generic fields.
- Architecture section just lists the tech stack without describing how components interact.

**Downstream dependencies:**
- Passed as the `prd` string to the Growth Check agent. The Growth Check reads the PRD to identify gaps — a weak PRD produces a weak Growth Check.
- Rendered as the main user-facing output document. This is the core value proposition of the application.

---

### Agent 7 — Growth Check: Role in the System

**Where it sits in the user journey:**
Final agent in the generate pipeline. Runs after the PRD is complete and reads both the PRD and the confirmed stack selections. Its output is the first thing the user sees on the Output page (shown above the PRD). It is an honest, opinionated senior-engineer review — the voice of someone who has shipped real systems and is pointing out what's solid, what could break, and what's missing.

**What it receives:**
- `prd`: the full markdown string from the PRD Generator
- `selections`: the confirmed stack `{scope, backend, frontend, apis, database}`

**What it produces:**
A structured JSON object rendered as 3 expandable cards in the UI. Each card has a coloured top border (green / amber / red) and a list of items. Items show a title by default; clicking expands the full detail text.

| Field | UI card | Colour |
|---|---|---|
| `good` | ✅ Good Choices | Green top border |
| `warnings` | ⚠️ Warnings | Amber top border |
| `missing` | ❌ Still Missing | Red top border |

Each item has:
- `title`: shown collapsed — the name of the choice, concern, or missing piece (≤6 words ideally)
- `detail`: shown expanded — 1-2 sentences of specific explanation

**What a good response looks like:**
- `good` items name a specific decision and explain *why it fits this system* (not why the technology is generally good).
- `warnings` name a concrete failure mode that could actually happen given this system's usage — not theoretical.
- `missing` only flags things that are genuinely absent from the PRD and stack that this system actually needs (e.g. rate limiting if an external API is used without throttling, not "you might want monitoring someday").
- Titles are short and scannable — the user can read all titles collapsed and understand the shape of the review.

**What a bad response looks like:**
- `good` items say things like "FastAPI is a good choice" with no project context.
- `warnings` are theoretical or apply to all projects ("you should consider security").
- `missing` flags nice-to-haves rather than genuine gaps ("you could add analytics").
- Item titles are full sentences that can't be scanned collapsed.

**Downstream dependencies:**
- This is the last LLM call in the pipeline. Nothing reads its output programmatically — it is purely for the user.
- Its quality directly determines how trustworthy the app feels. A growth check that is generic or inaccurate undermines confidence in the entire blueprint.

---

## Data Contracts Between Agents

This table shows exactly what each agent passes to the next, and what format that data takes. Use this when tracing quality issues back to their source agent.

| From | To | Data passed | Format |
|---|---|---|---|
| User (QuickSetup) | Recommender | `idea` (string) + `constraints` (dict) | Raw user input |
| Recommender | Context Advisor | `idea`, `constraints`, `recommended` dict | `{scope, backend, frontend, apis, database}` |
| Recommender | Option Advisor ×12 | `idea`, `constraints_block`, `stack_context` string, `field`, `value` | Per-option call |
| Recommender | Frontend state | All 8 recommendation fields | JSON object |
| Context Advisor | Frontend state | `deployment` array only | 3-item array |
| Option Advisor | Frontend state | `architecture` dict with per-option structure | `{field: {recommended, options: {value: {relevant, reason, benefits, drawbacks}}}}` |
| User (Generate click) | Normalizer | `idea` + `selections` dict | `{scope, backend, frontend, apis, database}` |
| Normalizer | Analyzer | Full normalized dict | `{system_name, purpose, core_features, user_types, constraints, assumptions_removed}` |
| Normalizer + Analyzer | PRD Generator | Both dicts | Passed as JSON in user message |
| PRD Generator | Growth Check | PRD markdown string + `selections` dict | Plain text + `{scope, backend, frontend, apis, database}` |
| PRD Generator | Frontend state | PRD markdown string | Rendered via ReactMarkdown |
| Growth Check | Frontend state | Structured review dict | `{good, warnings, missing}` — each an array of `{title, detail}` |
| env_builder (no LLM) | Frontend state | `.env` file string | Plain text, one `KEY=value` per line |
