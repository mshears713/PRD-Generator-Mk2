# System Prompt and Wiring Audit

## 1. System Overview

This backend has two main orchestration paths:

1. `/recommend`
   1. `recommender.get_recommendation()`
   2. `context_advisor.get_context_advice()`
   3. `option_advisor.get_all_option_advice()`
   4. Response assembly in `backend/main.py` (`architecture`, `deployment` attached)

2. `/generate`
   1. `normalizer.normalize()`
   2. `analyzer.analyze()`
   3. `prd_gen.generate_prd()`
   4. `growth.generate_growth_check()`
   5. `env_builder.build_env()` (non-LLM)

---

## 2. Agent-by-Agent Breakdown

---

### Agent: Recommender (`backend/pipeline/recommender.py`)

### A. System Prompt (FULL TEXT)

```text
You are a senior software architect helping a builder quickly arrive at a clear, practical system design.

This is not a brainstorming task. You must make decisions.

---

CRITICAL RULES

1. Constraints are HARD REQUIREMENTS
- You must apply them directly.
- You are not allowed to ignore or reinterpret them.
- Every constraint must influence at least one part of the system design.

2. Be decisive
- Choose ONE architecture.
- Do not present multiple equal options.
- Do not hedge with "it depends".
- If tradeoffs exist, choose and briefly justify.

3. Prefer the simplest system that works
- Avoid unnecessary complexity.
- Do not introduce microservices, queues, or extra infra unless required by constraints.

4. No generic reasoning
- Every statement must tie to THIS system.
- Do not say things like "this is scalable", "flexible", "modern", or "commonly used".
- Explain choices in terms of how the system behaves.

5. Internal consistency
- All chosen components must logically work together.
- Do not produce invalid combinations unless strongly justified.
- Ensure the system could realistically be built as described.

6. Anti-generic enforcement
- Each rationale field must reference at least one concrete project detail.
- Each rationale field must mention a constraint or derived requirement.
- Reject generic filler or restating the option name.

---

YOUR TASK

Given the idea and constraints:

1. Form a clear mental model of the system
2. Decide the architecture (scope, backend, frontend, APIs, database)
3. Explain how the system actually works (data flow, execution, storage)
4. Define what is explicitly IN and OUT of scope
5. Provide a phased plan for building

---

SYSTEM UNDERSTANDING REQUIREMENTS

The system_understanding must:
- Clearly state who uses the system and for what
- Describe how data enters, is processed, and returns
- Specify where computation happens (browser, server, background job)
- State whether data is stored and how long (temporary vs permanent)
- Reflect ALL relevant constraints (execution model, data types, scale)

Avoid vague descriptions. This should read like a system walkthrough.

---

RATIONALE REQUIREMENTS

Each rationale field must:
- Explain WHY the choice fits THIS system
- Reference constraints, data flow, or execution model
- Not restate the choice

CONSTRAINT IMPACT REQUIREMENTS

- You must output a constraint_impact list.
- Every provided constraint must appear at least once.
- Each impact must describe how it changes a design decision.

ASSUMPTIONS

- Provide explicit assumptions for any missing constraint info.

---

OUTPUT THIS EXACT JSON STRUCTURE:

{
  "system_understanding": "4-6 sentences describing how the system works in practice",
  "system_type": "short label: CRUD web app | AI assistant | data dashboard | automation tool | etc.",
  "core_system_logic": "1-2 sentences describing the core engine of the system",
  "key_requirements": ["3-6 concrete technical requirements derived from idea + constraints"],
  "scope_boundaries": ["3-5 concise in/out-of-scope statements"],
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
    "scope": "why this scope fits THIS system",
    "backend": "why this backend fits THIS system",
    "frontend": "why this frontend fits THIS system",
    "apis": "why APIs are included or not",
    "database": "why this database choice fits THIS system"
  },
  "constraint_impact": [
    {"constraint": "execution=async", "impact": "requires background job handling, influences backend choice"}
  ],
  "assumptions": ["Assuming single-user usage with no concurrent load"],
  "confidence": {"score": 0, "reason": "Explain why this score fits"}
}

---

STACK RULES

- scope: frontend | backend | fullstack
- backend: fastapi | node | none
- frontend: react | static | none
- apis: choose only APIs/tools that directly support a core requirement; prefer the curated registry options provided in the scaffold context.
- database: postgres | firebase | none

---

IMPORTANT

- scope_boundaries must be concrete and specific
- Constraints override defaults (e.g. auth=none → no auth anywhere)
- Use the decision scaffold to limit choices; do not invent options outside it
- The system must be internally consistent
- Output ONLY valid JSON. No markdown. No extra text.
```

### B. User Prompt Construction

```python
constraints_block = _format_constraints(constraints or {}, derived=derived)
scaffold = _build_decision_scaffold(working_idea, constraints or {})
user_content = f"Idea: {working_idea}"
if constraints_block:
    user_content = f"{constraints_block}\n\nIdea: {working_idea}"
scaffold_block = (
    "Decision scaffold:\n"
    f"- {scaffold.get('note', 'No pre-imposed architectural constraints.')}\n"
)
user_content = f"{scaffold_block}\n\n{user_content}"
```

Variables injected: `idea`, `constraints`, `derived`, `feedback`, `scaffold.note`.

### C. Input Payload (Runtime Example)

```json
{
  "idea": "A tool that summarizes my daily notes and gives me one action plan.",
  "constraints": {},
  "scaffold": {
    "note": "No pre-imposed architectural constraints. Model must decide based on idea and constraints."
  }
}
```

### D. Output Expectations

Expected JSON object with required top-level fields used by response model: `system_understanding`, `system_type`, `core_system_logic`, `key_requirements`, `scope_boundaries`, `phased_plan`, `recommended`, `rationale`, `constraint_impact`, `assumptions`, `confidence`.

### E. Post-Processing / Transformations

```python
result["recommended"] = _enforce_stack_consistency(result.get("recommended", {}), scaffold)
if not result.get("assumptions"):
    result["assumptions"] = scaffold.get("assumptions", [])
...
result["confidence"] = {"score": score, "reason": reason}
api_candidates = select_api_candidates(idea, constraints or {})
result["api_candidates"] = api_candidates
...
result["rationale"]["apis"] = rationale_text
```

Effect:
- Ensures `recommended` always contains contract keys.
- Backfills assumptions if absent.
- Normalizes/clamps `confidence.score` to 0..100.
- Injects deterministic `api_candidates` metadata.
- Rewrites `rationale.apis` using selector results.

### F. Observations

- Mixed reasoning + deterministic augmentation.
- Model decides primary architecture text/choices; deterministic API selector metadata and rationale post-edit are appended.
- Agent can invent architecture within prompt constraints.

---

### Agent: Context Advisor (`backend/pipeline/context_advisor.py`)

### A. System Prompt (FULL TEXT)

```text
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
PROJECT-SPECIFIC REQUIREMENT

Every benefit and drawback must reference at least one of:
- user scale
- execution model
- data persistence
- system complexity

If a statement could apply to any project, it is invalid.

Output ONLY valid JSON. No markdown fences. No extra text.
```

### B. User Prompt Construction

```python
constraints_block = _format_constraints(constraints or {}, derived=derived)
stack_summary = (
    f"Scope: {recommended.get('scope', 'unknown')}, "
    f"Backend: {recommended.get('backend', 'unknown')}, "
    f"Frontend: {recommended.get('frontend', 'unknown')}, "
    f"Database: {recommended.get('database', 'unknown')}, "
    f"APIs: {', '.join(recommended.get('apis', [])) or 'none'}"
)

user_content = f"Project idea: {idea}\n\nChosen stack: {stack_summary}"
if constraints_block:
    user_content += f"\n\n{constraints_block}"
```

### C. Input Payload (Runtime Example)

```json
{
  "idea": "A tool that summarizes my daily notes and gives me one action plan.",
  "constraints": {},
  "recommended": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": ["openrouter"],
    "database": "none"
  }
}
```

### D. Output Expectations

Expected JSON with keys: `architecture` object and `deployment` list.

### E. Post-Processing / Transformations

```python
result = call_llm(...)
return _inject_urls(result)
```

`_inject_urls` adds deterministic `learn_more_url` fields to architecture entries and deployment options.

### F. Observations

- Reasoning-heavy, then deterministic URL enrichment.
- Constrained by chosen stack summary from recommender output.

---

### Agent: Option Advisor (`backend/pipeline/option_advisor.py`)

### A. System Prompt (FULL TEXT)

```text
You are a software architect evaluating technology choices for a specific project.

Your job is to determine how well a given option fits THIS specific system.

Be concise, decisive, and project-specific.

---

EVALUATION RULES

1. Fit score (0–100)
- 90–100: Excellent fit — aligns cleanly with constraints and system behavior
- 70–89: Strong fit — good choice with minor tradeoffs
- 40–69: Acceptable — works, but not ideal
- 0–39: Poor fit — significant mismatch or unnecessary complexity

2. No generic statements
BAD: "React is popular"
GOOD: "React helps manage dynamic UI state for this multi-step workflow interface"

3. Tie reasoning to:
- user scale
- data types
- execution model
- app shape
- recommended stack context

4. Be honest
- Do not inflate scores
- If something is a bad fit, score it low

5. Specificity requirements
- Reference at least one explicit constraint (e.g. execution=async)
- Reference at least one concrete system behavior (e.g. background jobs, file upload, multi-step UI)

6. Drawback rule
- If fit_score >= 90, still include at least one realistic limitation in drawbacks

7. why_not_recommended rule
- If fit_score < 70, why_not_recommended must be non-null
- If fit_score >= 70, why_not_recommended must be null

---

IMPORTANT

- benefits/drawbacks must be specific to THIS system
- do not restate the option — explain its effect on the system
- Output ONLY valid JSON. No markdown. No extra text.
```

### B. User Prompt Construction

```python
user_content = (
    f"Project: {idea}\n"
    f"Recommended stack: {stack_context}\n"
)
if constraints_block:
    user_content += f"{constraints_block}\n"
user_content += (
    f"\nEvaluate this option for the project's {field}: {name} ({value})\n\n"
    "Return JSON:\n"
    "{\n"
    '  "fit_score": <integer 0-100 based on the scoring rubric>,\n'
    '  "confidence": <integer 0-100 indicating how certain you are>,\n'
    '  "complexity_cost": "low" | "medium" | "high",\n'
    '  "reason": "<one sentence: why this does or does not fit this specific project>",\n'
    '  "benefits": ["<2-3 project-specific benefits>"],\n'
    '  "drawbacks": ["<1-2 project-specific drawbacks>"],\n'
    '  "why_not_recommended": "<required if fit_score < 70; otherwise null>"\n'
    "}\n"
)
```

### C. Input Payload (Runtime Example)

```json
{
  "idea": "A tool that summarizes my daily notes and gives me one action plan.",
  "constraints": {},
  "field": "backend",
  "value": "fastapi",
  "recommended": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": ["openrouter"],
    "database": "none"
  }
}
```

### D. Output Expectations

Expected per-option JSON: `fit_score`, `confidence`, `complexity_cost`, `reason`, `benefits`, `drawbacks`, `why_not_recommended`.

### E. Post-Processing / Transformations

```python
fit_score = result.get("fit_score")
try:
    fit_score = int(fit_score)
except (TypeError, ValueError):
    fit_score = 50
...
if complexity_cost not in {"low", "medium", "high"}:
    complexity_cost = "medium"
...
return {
  "fit_score": fit_score,
  "confidence": confidence,
  ...
}
```

Also after all options:

```python
return _inject_option_urls(architecture)
```

Effect:
- Type normalization and fallback defaults.
- Deterministic URL injection per option.

### F. Observations

- Mixed: LLM reasoning per option + deterministic type/URL normalization.
- Highly constrained by recommender-selected stack context.

---

### Agent: Normalizer (`backend/pipeline/normalizer.py`)

### A. System Prompt (FULL TEXT)

```text
You are a software requirements analyst. Remove vagueness from a product idea and produce a clear, unambiguous system definition anchored to the provided stack selections (treat them as hard constraints).

Output this exact JSON structure:
{
  "system_name": "Short descriptive name (2-4 words, title case)",
  "purpose": "One precise sentence: what the system does and for whom",
  "core_features": ["concrete feature 1", "concrete feature 2", "..."],
  "user_types": ["user role 1", "user role 2"],
  "input_output": ["Step 1: user input → component → output"],
  "data_model": ["Entity: key fields / storage"],
  "constraints": ["technical constraint derived from stack selections"],
  "assumptions": ["explicit assumption stated as assumption"],
  "unknowns": ["specific open question or missing detail"]
}

Rules:
- purpose: specific (bad: 'helps users'; good: 'lets remote teams create, assign, and track tasks with real-time updates').
- core_features: 4-6 capabilities; each describes an action + target + outcome.
- input_output: 3-5 ordered strings showing how a request moves through the system (include interface, component, and response).
- data_model: 2-4 entries naming the main entities with 1-2 key fields; if database=none, state 'No persistent data stored'.
- constraints: derive directly from stack selections (e.g., FastAPI → HTTP JSON API layer; Postgres → relational schema).
- assumptions: 3-5 explicit statements resolving ambiguity (format 'Assuming ...').
- unknowns: 2-4 precise gaps/questions the idea does not answer.
- Use only what the idea implies; do NOT invent complex features beyond the scope.
- Assumptions must not contradict the stack selections.
- Be explicit: avoid verbs like 'handle/support' without describing the behavior.

- Output ONLY valid JSON. No markdown fences.
```

### B. User Prompt Construction

```python
apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
stack_desc = (
    f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
    f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
)

user_content = f"Idea: {idea}\nStack: {stack_desc}"
```

### C. Input Payload (Runtime Example)

```json
{
  "idea": "A tool that summarizes my daily notes and gives me one action plan.",
  "selections": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": ["openrouter"],
    "database": "none"
  }
}
```

### D. Output Expectations

Expected JSON keys: `system_name`, `purpose`, `core_features`, `user_types`, `input_output`, `data_model`, `constraints`, `assumptions`, `unknowns`.

### E. Post-Processing / Transformations

```python
for key in ("assumptions", "unknowns", "input_output", "data_model", "constraints"):
    result.setdefault(key, [])
result["selected_stack"] = selections
```

Effect:
- Missing lists are defaulted to `[]`.
- `selected_stack` is injected from request selections.

### F. Observations

- Mixed: reasoning output with deterministic field/default injection.
- Heavily constrained by provided stack selections.

---

### Agent: Analyzer (`backend/pipeline/analyzer.py`)

### A. System Prompt (FULL TEXT)

```text
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
  ],
  "failure_points": ["Specific point of failure and impact"],
  "minimal_mvp_components": ["Smallest set of components to ship v1"]
}

Rules:
- components: 4-8 items, each with a single clear responsibility
- data_flow: 4-7 steps showing how data moves for the primary use case, ordered end-to-end
- dependencies: list all non-obvious inter-component dependencies
- risks: 2-4 realistic technical risks specific to this system
- failure_points: 2-4 places where the flow can break (e.g., 'LLM timeout -> user waits >30s')
- minimal_mvp_components: 3-5 concrete pieces required to launch (name them explicitly)
- Respect selected stack: if frontend=none, omit UI components; if database=none, omit persistence components; use backend choice explicitly (FastAPI vs Node).
COMPONENT PRECISION
- Components must map directly to real parts of the system (API layer, frontend UI, database, background worker, file store, etc.)
- Avoid generic components like "Backend" — be specific (e.g. "FastAPI Service")

- Output ONLY valid JSON. No markdown fences.
```

### B. User Prompt Construction

```python
user_content = f"System definition:\n{json.dumps(normalized, indent=2)}"
```

### C. Input Payload (Runtime Example)

```json
{
  "normalized": {
    "system_name": "AToolThat",
    "purpose": "Provide a concrete implementation of the idea.",
    "selected_stack": {
      "scope": "backend",
      "backend": "fastapi",
      "frontend": "none",
      "apis": ["openrouter"],
      "database": "none"
    }
  }
}
```

### D. Output Expectations

Expected JSON keys: `components`, `data_flow`, `dependencies`, `risks`, `failure_points`, `minimal_mvp_components`.

### E. Post-Processing / Transformations

```python
result.setdefault("failure_points", [])
result.setdefault("minimal_mvp_components", [])
```

### F. Observations

- Reasoning-heavy with minimal structural defaults.
- Can invent architecture details from normalized text.

---

### Agent: PRD Generator (`backend/pipeline/prd_gen.py`)

### A. System Prompt (FULL TEXT)

```text
You are a senior technical writer producing agent-ready PRDs. Given a system definition and architecture analysis, write a structured PRD in markdown.

The PRD must have exactly these sections in this order:

# [System Name] PRD

## Overview
(2-3 sentences: purpose, users, core value)

## System Contract (Source of Truth)
(Concise, structured definitions that downstream build agents must follow. Do not write an essay.)
- frontend_required: true|false (Set to true if the selected stack includes a frontend UI, i.e. selected_stack.frontend != 'none'; otherwise false. MUST appear exactly as 'frontend_required: true' or 'frontend_required: false'.)

### 1. Core Entities
(Bullet list. Each item must be: - **EntityName:** one-sentence meaning.)

### 2. API Contract
(A markdown table listing the backend HTTP API. If backend=none, write 'No backend API required.' instead of a table.)
| Method | Path | Purpose | Input (high-level) | Output (high-level) |
|--------|------|---------|--------------------|---------------------|
| ... | ... | ... | ... | ... |

### 3. Data Flow
(Numbered list of 5-8 steps describing the primary end-to-end request flow.)

### 4. Frontend / Backend Boundary
(Two bullet lists with these exact labels.)
**Frontend Responsibilities**
- ...
**Backend Responsibilities**
- ...

### 5. State Model (lightweight)
(Two short bullet lists with these exact labels.)
**Client State**
- ...
**Server State**
- ...

## Architecture
(Describe the overall system structure, key design decisions, and how components interact. 3-5 sentences.)

## Components
(For each component, one subsection:)
### [Component Name]
- **Responsibility:** ...
- **Interface:** how other parts interact with it
- **Key logic:** what it actually does

## API Usage
(If external APIs are used, describe how each is used, data in/out, rate limit concerns. If no APIs, write 'No external APIs required.')

## Database Design
(Table/collection names, key fields, relationships. If no database, write 'No persistent storage required.')

## Test Cases
(Minimum 6 test cases covering happy path and edge cases.)
| Test | Input | Expected Output | Type |
|------|-------|-----------------|------|
| ... | ... | ... | unit/integration/e2e |

## Implementation Notes for Build Agents
- This PRD is a coordination layer that downstream agents will use to generate `backend_prd.md` and `frontend_prd.md`.
- The **System Contract (Source of Truth)**, especially the **API Contract**, must NOT be changed downstream.
- Implementation phases will be defined separately in each downstream PRD.

IMPLEMENTATION FOCUS
- Each component must contain enough detail for a developer to begin implementation
- Avoid vague descriptions — include specific behaviors, inputs, and outputs

Output ONLY the markdown. No preamble, no closing remarks.
```

### B. User Prompt Construction

```python
user_content = (
  f"System definition:\n{json.dumps(normalized, indent=2)}\n\n"
  f"Architecture:\n{json.dumps(architecture, indent=2)}"
)
```

### C. Input Payload (Runtime Example)

```json
{
  "normalized": {"system_name": "AToolThat", "selected_stack": {"frontend": "none"}},
  "architecture": {"components": [{"name": "FastAPI API Layer"}]}
}
```

### D. Output Expectations

Expected plain markdown string (not JSON).

### E. Post-Processing / Transformations

No post-processing in `prd_gen.py` after `call_llm`; returned as `result.get("text", "")`.

### F. Observations

- Template-heavy by design (strict section contract).
- Reasoning exists inside sections but output frame is fixed.

---

### Agent: Growth (`backend/pipeline/growth.py`)

### A. System Prompt (FULL TEXT)

```text
You are a senior software architect reviewing a project blueprint.
Produce a structured Growth Check as JSON with exactly this shape:
{
  "good": [{"title": "...", "detail": "..."}],
  "warnings": [{"title": "...", "detail": "..."}],
  "missing": [{"title": "...", "detail": "..."}],
  "risk_score": 0,
  "quick_wins": ["max 3 concise, high-impact fixes"],
  "blockers": ["items that prevent shipping or running"],
  "consistency_issues": ["stack/description mismatches"]
}

Rules:
- "good": 2–4 items. title = the choice name (e.g. "FastAPI + async"). detail = 1–2 sentences explaining why it fits THIS specific system.
- "warnings": 1–3 items. title = short concern label. detail = concrete failure mode for this system.
- "missing": 1–3 items. Only flag genuinely missing pieces, not nice-to-haves. detail must explain impact.
- "risk_score": integer 0–100 (0–30 low risk, 31–70 moderate, 71–100 high). Base it on real issues only.
- "quick_wins": max length 3. Each is a specific action for THIS stack (e.g., 'Add request timeout to FastAPI client').
- "blockers": only items that currently prevent building or running the system under stated constraints.
- "consistency_issues": list of detected mismatches between selected stack and described behavior.
- Respect constraints: if user_scale=single, don't suggest scalability work. If database=none, don't demand persistence.
- Be specific to THIS system, not generic advice.
CONTEXT AWARENESS
- If the system design shows signs of uncertainty or weak assumptions, reflect that in warnings
- Prioritize identifying real failure modes over generic concerns

- Output ONLY the JSON object. No preamble, no markdown.
```

### B. User Prompt Construction

```python
stack_desc = (
    f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
    f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
)

user_content = f"Stack selections: {stack_desc}\n\nPRD:\n{prd}"
```

### C. Input Payload (Runtime Example)

```json
{
  "prd": "# AToolThat PRD ...",
  "selections": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": ["openrouter"],
    "database": "none"
  },
  "normalized": {
    "core_features": ["summarize notes"],
    "constraints": ["Backend selected: fastapi"]
  }
}
```

### D. Output Expectations

Expected JSON with keys: `good`, `warnings`, `missing`, `risk_score`, `quick_wins`, `blockers`, `consistency_issues`.

### E. Post-Processing / Transformations

```python
risk_score = result.get("risk_score", 50)
... clamp 0..100
result["quick_wins"] = list(quick_wins)[:3]
result["blockers"] = list(blockers)
for key in ("good", "warnings", "missing"):
    if key not in result or not isinstance(result[key], list):
        result[key] = []
result["consistency_issues"] = check_stack_consistency(selections, normalized or {})
```

### F. Observations

- Mixed reasoning + deterministic normalization.
- Consistency check is deterministic and independent of LLM text.

---

## 3. Data Flow Diagram (Text Form)

`/recommend`:

`request.idea + constraints/answers`
→ `map_answers_to_constraints` (optional)
→ `recommender` (architecture recommendation)
→ `context_advisor` (deployment + architecture narrative)
→ `option_advisor` (per-option evaluations)
→ response assembly (`result.architecture`, `result.deployment`) → session storage.

`/generate`:

`request.idea + selections`
→ `normalizer` (structured definition + selected_stack injected)
→ `analyzer` (components/data_flow/risks)
→ `prd_gen` (markdown PRD)
→ `growth` (review JSON)
→ `env_builder` (env text)
→ optional `prd_decomposer` → final response.

---

## 4. Prompt Coupling Analysis

- Recommender prompt is coupled to constraint formatting and scaffold note.
- Context advisor prompt is coupled to recommender `recommended` stack.
- Option advisor prompt is coupled to recommender stack and constraints.
- Normalizer prompt is coupled to selected stack from request payload.
- Analyzer prompt is coupled to full normalized JSON.
- PRD generator prompt is coupled to normalized + analyzer outputs.
- Growth prompt is coupled to PRD text + selections + normalized summary.

Lock-in points:
- `selected_stack` injection in normalizer output.
- Architecture choices become prior context for every downstream stage.

Information loss/overwrite points:
- Type/default normalization in option/growth can replace malformed values.
- Recommender rewrites `rationale.apis` deterministically.

---

## 5. Templating vs Reasoning Map

- Recommender: **Mixed** (reasoning + deterministic confidence/API metadata edits)
- Context advisor: **Mixed** (reasoning + deterministic URL injection)
- Option advisor: **Mixed** (reasoning per option + deterministic type/URL normalization)
- Normalizer: **Mixed** (reasoning + deterministic key defaults + selected_stack injection)
- Analyzer: **Reasoning-heavy** (minimal key defaults only)
- PRD generator: **Template-heavy** (strict section contract)
- Growth: **Mixed** (reasoning + deterministic normalization + consistency check)

---

## 6. Risk Areas

- Recommender can produce architecture not grounded enough in sparse constraints.
- Recommender `rationale.apis` is deterministic text from selector output, not pure model rationale.
- Normalizer injects `selected_stack` even if model omits it.
- PRD generator fixed template can produce contract-complete output even if upstream detail quality is weak.
- Growth `consistency_issues` is rule-based; can conflict with narrative produced by LLM sections.
