# CodeGarden — LLM Agent Reference_v2

This document is a tuning and implementation addendum to the original **CodeGarden — LLM Agent Reference** file. It is not a replacement for the original reference. It should be used alongside the existing agent file as the implementation guide for the next tuning pass.

## Purpose of this v2 document

This version captures the agreed prompt and output-shape changes discussed after reviewing the current pipeline. The goal is not to redesign Codegarden or expand scope. The goal is to improve output quality while preserving the existing product behavior:

- make the system more decisive
- force tighter use of constraints
- reduce generic and reusable fluff
- improve recommendation quality without overcomplicating the architecture
- improve option-level evaluation in the UI
- preserve the current pipeline shape unless explicitly noted

## Product stance being preserved

Codegarden remains:

- a software planning decision engine
- optimized for hackathons, personal tools, AI-assisted builds, and fast iteration
- biased toward the simplest buildable system that works

Codegarden is still **not** a generic assistant, vague consultant, or enterprise architecture generator.

---

## Global implementation guidance

Apply these principles across all agent prompts where relevant:

1. **Constraints are hard inputs, not soft preferences.**
   - The selected constraints must visibly shape architecture, storage, execution, and scope.
   - Do not let agents “creatively reinterpret” them.

2. **Prefer the simplest viable system.**
   - No microservices, complex infra, queues, or extra abstractions unless the constraints clearly require them.

3. **Every statement should be project-specific.**
   - If a sentence could be copied into another project unchanged, it is probably too generic.

4. **System-first reasoning beats feature-listing.**
   - Prioritize behavior, data flow, execution location, and storage decisions.

5. **Be decisive, but not sloppy.**
   - Commit to one recommendation when the product calls for one.
   - Acknowledge ambiguity through scoring/confidence rather than hedging language.

---

# Pipeline-level changes

## 1. Recommender remains a single agent

This was reviewed directly.

Decision:
- Keep the Recommender as one agent for now.
- Do **not** split it into multiple “voter” or “sub-decision” agents yet.

Reason:
- It is still useful to have one source of truth for the initial stack recommendation.
- Splitting too early would increase debugging complexity and risk inconsistent recommendations.

## 2. Add confidence to the Recommender

Add a new top-level field:

```json
"confidence": 0.0
```

Purpose:
- indicate how strongly the recommender believes the chosen architecture fits the idea + constraints
- support downstream interpretation later, especially in Growth Check
- allow future UI treatment for low-confidence recommendations

Interpretation:
- `0.8–1.0` = clear idea, clean constraint alignment, straightforward architecture
- `0.5–0.7` = some ambiguity or meaningful tradeoffs
- `<0.5` = missing critical detail, conflicting constraints, or more assumptions required

## 3. Add fit scoring to the Option Advisor

Add a new field:

```json
"fit_score": 0
```

Keep the existing `relevant` field for compatibility, but derive it from `fit_score`:
- `fit_score < 20` → `relevant = false`
- otherwise → `relevant = true`

Decision preserved:
- keep the “recommended” option coming from the Recommender for now
- do **not** auto-promote the highest `fit_score` to recommended yet

Purpose:
- make option cards more independently evaluative
- improve filtering quality without changing the overall recommendation model
- allow more nuanced judgments than simple relevant / not relevant

---

# Agent-by-agent changes

## Agent 1 — Recommender

### Status
Major tuning pass.

### Keep
- single-agent role
- same overall responsibility
- same core JSON structure, with one added field: `confidence`

### Problems in the current prompt
- “Be decisive” is requested but not enforced strongly enough
- constraints are labeled hard requirements, but not operationalized tightly enough
- `system_understanding` can drift into generic product-summary language
- rationale can become generic restatement
- no explicit confidence/self-awareness field
- no explicit internal consistency guardrail

### Required changes

#### A. Add stronger behavioral framing
The prompt should clearly state:
- this is not brainstorming
- the agent must make decisions
- no equal-option presenting unless absolutely necessary
- no “it depends” without still choosing a primary recommendation

#### B. Make constraints operational
Add a hard rule that:
- every provided constraint must influence at least one part of the output
- the model is not allowed to ignore or reinterpret constraints casually

#### C. Tighten `system_understanding`
The prompt should require that `system_understanding` covers:
- who uses the system and for what
- how data enters, is processed, and returns
- where computation happens: browser, server, or background job
- whether data is stored and whether it is temporary or persistent
- visible reflection of execution model, data types, and scale constraints

This should read like a short system walkthrough, not a marketing summary.

#### D. Tighten rationale quality
Each rationale field must:
- explain why the choice fits this specific system
- reference constraints, data flow, or execution model
- avoid generic praise or simple restatement

#### E. Add confidence
Add:

```json
"confidence": 0.0
```

#### F. Add internal consistency rule
Add a rule such as:
- all chosen components must logically work together
- avoid invalid combinations unless strongly justified
- the resulting recommendation should be realistically buildable as described

### Updated recommended system prompt

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
- Do not hedge with “it depends”.
- If tradeoffs exist, choose and briefly justify.

3. Prefer the simplest system that works
- Avoid unnecessary complexity.
- Do not introduce microservices, queues, or extra infra unless required by constraints.

4. No generic reasoning
- Every statement must tie to THIS system.
- Do not say things like “this is scalable” or “commonly used”.
- Explain choices in terms of how the system behaves.

5. Internal consistency
- All chosen components must logically work together.
- Do not produce invalid combinations unless strongly justified.
- Ensure the system could realistically be built as described.

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

---

CONFIDENCE

You must output a confidence score between 0 and 1.

High confidence (0.8–1.0):
- Idea is clear
- Constraints align cleanly
- Architecture is straightforward

Medium confidence (0.5–0.7):
- Some ambiguity in idea
- Tradeoffs between multiple reasonable approaches

Low confidence (<0.5):
- Missing critical details
- Conflicting constraints
- Architecture assumptions required

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
  "confidence": 0.0
}

---

STACK RULES

- scope: frontend | backend | fullstack
- backend: fastapi | node | none
- frontend: react | static | none
- apis: include 'openrouter' ONLY if LLM is core to the system
- apis: include 'tavily' ONLY if web search is required
- database: postgres | firebase | none

---

IMPORTANT

- scope_boundaries must be concrete and specific
- Constraints override defaults (e.g. auth=none → no auth anywhere)
- The system must be internally consistent
- Output ONLY valid JSON. No markdown. No extra text.
```

### Implementation notes
- Update any response model or parser for the added `confidence` field.
- Preserve downstream compatibility for all existing fields.
- Confidence does not need immediate UI rendering if not desired, but it should be available in the API response.

---

## Agent 2 — Context Advisor

### Status
Minor tuning pass.

### Keep
- same role
- same JSON structure
- same deployment recommendation rules
- exactly one deployment option recommended

### Problems in the current prompt
- can still produce generic benefits/drawbacks
- may write hosting commentary that sounds like general platform marketing

### Required changes
Add a project-specificity rule such as:
- every benefit and drawback must reference at least one of:
  - user scale
  - execution model
  - data persistence
  - system complexity
- if a sentence could apply to almost any project, it is invalid

### Suggested prompt addition

```text
PROJECT-SPECIFIC REQUIREMENT

Every benefit and drawback must reference at least one of:
- user scale
- execution model
- data persistence
- system complexity

If a statement could apply to any project, it is invalid.
```

### Implementation notes
- No schema changes required.
- Production still only uses the `deployment` portion.

---

## Agent 3 — Option Advisor

### Status
Major tuning pass.

### Keep
- same role in pipeline
- same per-option evaluation pattern
- same compatibility with UI card system
- `recommended` still comes from Recommender

### Problems in the current prompt
- only binary relevance, not graded fit
- easy to generate generic pros/cons
- can over-filter or under-explain
- too reactive to the recommended stack without enough independent evaluation pressure

### Required changes

#### A. Add `fit_score`
New output field:

```json
"fit_score": 0
```

Scoring meaning:
- `90–100` = excellent fit
- `70–89` = strong fit
- `40–69` = acceptable but not ideal
- `20–39` = weak fit
- `0–19` = poor fit

#### B. Keep `relevant`, but derive it from score
- `fit_score < 20` → `relevant = false`
- otherwise → `relevant = true`

#### C. Make evaluation explicitly project-specific
Require reasoning tied to:
- user scale
- data types
- execution model
- app shape
- recommended stack context

#### D. Explicitly tell the agent not to inflate scores
This is important so everything does not become a 78–92 mush zone.

### Updated recommended system prompt

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
- 20–39: Weak fit — significant mismatch
- 0–19: Poor fit — should not be used

2. Relevance
- If fit_score < 20 → relevant = false
- Otherwise → relevant = true

3. No generic statements
BAD: "React is popular"
GOOD: "React helps manage dynamic UI state for this multi-step workflow interface"

4. Tie reasoning to:
- user scale
- data types
- execution model
- app shape
- recommended stack context

5. Be honest
- Do not inflate scores
- If something is a bad fit, score it low

---

Return JSON:

{
  "fit_score": 0,
  "relevant": true,
  "reason": "one sentence explaining fit for THIS project",
  "benefits": ["2-3 project-specific benefits"],
  "drawbacks": ["1-2 project-specific drawbacks"]
}

---

IMPORTANT

- "relevant" must match the fit_score rule
- benefits/drawbacks must be specific to THIS system
- do not restate the option — explain its effect on the system
- Output ONLY valid JSON. No markdown. No extra text.
```

### Implementation notes
- Update UI/backend typing to accept `fit_score`.
- Continue using the Recommender’s recommendation as the starred/default option.
- Hide options where `fit_score < 20` by mapping to `relevant = false`.
- This change should not require a major UX rewrite if current filtering already keys off `relevant`.

---

## Agent 4 — Normalizer

### Status
Minor tuning pass.

### Keep
- same role
- same schema
- same place in pipeline

### Problems in the current prompt
- can still allow vague terms to survive normalization
- may produce feature language that sounds clean but is still not buildable

### Required changes
Add a stronger clarity requirement:
- replace vague language with concrete system behavior
- if the idea is ambiguous, make a reasonable assumption and state it clearly
- avoid verbs like “manage”, “handle”, or “support” unless the prompt specifies how

### Suggested prompt addition

```text
CLARITY REQUIREMENT

- Replace all vague terms with concrete system behavior
- If the idea is ambiguous, make a reasonable assumption and state it clearly
- Avoid phrases like "manage", "handle", "support" without specifying how
```

### Implementation notes
- No schema changes required.
- This should improve Analyzer and PRD Generator quality downstream.

---

## Agent 5 — Analyzer

### Status
Minor tuning pass.

### Keep
- same role
- same schema
- same output structure

### Problems in the current prompt
- components can become too abstract
- architecture may read like a summary instead of a build map

### Required changes
Force components to map to real system parts.
Avoid generic labels like “Backend” when a more concrete component name is appropriate.

### Suggested prompt addition

```text
COMPONENT PRECISION

- Components must map directly to real parts of the system (API layer, frontend UI, database, background worker, file store, etc.)
- Avoid generic components like "Backend" — be specific (e.g. "FastAPI Service")
```

### Implementation notes
- No schema changes required.
- This is mainly a specificity improvement for the PRD stage.

---

## Agent 6 — PRD Generator

### Status
Minor tuning pass.

### Keep
- same role
- same markdown output
- same section ordering
- same overall contract

### Problems in the current prompt
- components can still be described too thinly
- implementation utility can vary too much

### Required changes
Strengthen implementation detail expectations:
- each component should contain enough detail for a developer to begin implementation
- avoid vague descriptions
- include more specific behaviors, inputs, and outputs where natural

### Suggested prompt addition

```text
IMPLEMENTATION FOCUS

- Each component must contain enough detail for a developer to begin implementation
- Avoid vague descriptions — include specific behaviors, inputs, and outputs
```

### Implementation notes
- No schema change.
- This is intended to improve handoff usefulness without making the PRD bloated.

---

## Agent 7 — Growth Check

### Status
Minor tuning pass now, with room for a stronger v3 later.

### Keep
- same role
- same schema
- same UI usage

### Problems in the current prompt
- can drift toward generic review language
- may flag broad best practices instead of real failure modes
- currently does not benefit from Recommender confidence, though that should become possible later

### Required changes
Sharpen the review style:
- prioritize concrete failure modes over generic concerns
- if the system design appears assumption-heavy or uncertain, reflect that in warnings
- only call out genuinely missing pieces, not nice-to-haves

### Suggested prompt addition

```text
CONTEXT AWARENESS

- If the system design shows signs of uncertainty or weak assumptions, reflect that in warnings
- Prioritize identifying real failure modes over generic concerns
```

### Implementation notes
- No immediate schema change.
- Recommended future improvement: pass Recommender confidence into Growth Check context so it can tune its warning intensity.

---

# Output contract changes summary

## Recommender output
Add:

```json
"confidence": 0.0
```

## Option Advisor output
Add:

```json
"fit_score": 0
```

Retain:

```json
"relevant": true
```

But derive `relevant` from `fit_score` using the rule above.

---

# Recommended implementation order

1. **Recommender prompt update**
   - highest leverage
   - add confidence

2. **Option Advisor prompt + parser update**
   - add fit_score
   - derive relevant from threshold

3. **Light prompt additions for Context Advisor, Normalizer, Analyzer, PRD Generator, and Growth Check**
   - low-risk specificity improvements

4. **Optional later step**
   - expose Recommender confidence to Growth Check and possibly UI

---

# What is intentionally not changing in v2

These were considered and explicitly deferred:

- splitting Recommender into multiple agents
- changing the recommended option source from Recommender to Option Advisor
- major pipeline restructuring
- changing Context Advisor’s production role beyond prompt tightening
- adding confidence/score UI treatment immediately

This v2 pass is intended to improve quality while preserving current architecture and product flow.

---

# Final implementation intent

The coding agent should use this file together with the original **CodeGarden — LLM Agent Reference**.

Working rule:
- treat the original file as the baseline description of the current system
- treat this v2 file as the approved change set for the next tuning pass

