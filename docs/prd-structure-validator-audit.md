# PRD Structure Validator Audit

## 1) Exact file/function where the runtime error is raised

- **File:** `backend/pipeline/prd_contract.py`
- **Function:** `extract_system_contract_section(main_prd: str)`
- **Raise site:** when regex for `## System Contract (Source of Truth)` is not found.
- **Exact error:** `Main PRD missing '## System Contract (Source of Truth)' section.`

---

## 2) Every place that assumes fixed PRD headings

### Runtime parser/validator logic (production path)

1. `backend/pipeline/prd_contract.py`
   - Requires H2: `## System Contract (Source of Truth)`.
   - Requires H3 order inside contract section:
     - `### 1. Core Entities`
     - `### 2. API Contract`
     - `### 3. Data Flow`
   - Requires API table header (`| Method | Path |`) **or** exact fallback text `No backend API required.`
   - Requires line: `- frontend_required: true|false`.

2. `backend/pipeline/prd_decomposer.py`
   - Always calls `extract_system_contract_section(main_prd)` first.
   - Then always calls `extract_core_entities_block(contract_section)` and `extract_api_contract_block(contract_section)`.
   - This means decomposition depends on the fixed contract subsection headings and API section format.

3. `backend/main.py`
   - `/generate` calls `decompose_prds(...)` when `prd_decomposition_enabled()` is true (default true).
   - So heading validation is part of normal runtime unless decomposition is disabled.

### Prompt/test assumptions that reinforce fixed headings

4. `backend/tests/test_prd_gen.py`
   - Expects many exact headings in generated PRD (`Overview`, `System Contract`, numbered contract subsections, `Architecture`, `Components`, `Test Cases`, `Implementation Notes for Build Agents`).

5. `backend/tests/test_prd_contract.py`
   - Uses contract fixtures with exact numbered headings and API table shape.

6. `backend/llm.py` (fake LLM path for tests)
   - `_fake_prd_gen` emits the old fixed heading template, including `### 1/2/3` contract subsections and implementation notes.

---

## 3) Which headings are required vs optional in code

## Required at runtime (with decomposition enabled)

- `## System Contract (Source of Truth)` (hard required).
- Inside contract section:
  - `### 1. Core Entities` (required by extractor).
  - `### 2. API Contract` (required by extractor).
  - `### 3. Data Flow` (required as boundary marker for API extractor).
- `- frontend_required: true|false` line in contract section.
- API contract body must contain either:
  - a markdown table with `| Method | Path | ...`, or
  - exact textual fallback `No backend API required.`

## Not required by runtime validators

- `## Overview`
- `## Architecture`
- `## Components`
- `## Test Cases`
- `## Implementation Notes...`

(These are currently expected by tests/fake-output conventions, not by the runtime contract extractor.)

---

## 4) Is current prompt behavior incompatible with current validators?

- **Yes, potentially incompatible.**
- Current `backend/pipeline/prd_gen.py` prompt says structure is adaptive and section order is not fixed.
- But runtime decomposition still expects a fixed `System Contract` block with fixed numbered subheadings and API-contract formatting.
- If the LLM follows flexible behavior and omits/renames these exact headings, decomposition can raise the runtime error immediately.

---

## 5) Minimal recommendation (no code changes yet)

Choose one simple path:

1. **Restore required contract headings in prompt (lowest-risk now).**
   - Keep flexible PRD globally, but make `System Contract` subsection format explicit and fixed for decomposer compatibility.

or

2. **Relax validator logic (more robust long-term).**
   - Make `prd_contract.py` tolerant to heading variants/absence and use stack fallbacks without hard failure.

### Suggested immediate choice

- **Option 1** is the smallest, fastest fix for the current runtime error with minimal blast radius.
