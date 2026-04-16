# Pipeline Debiasing Changes

## 1) Summary of changes made

- `backend/pipeline/recommender.py`
  - `_build_decision_scaffold` now returns a minimal neutral note.
  - Removed architecture forcing data (`requires_*`, `allowed_*`, `preferred_*`, required API injection).
  - `_enforce_stack_consistency` is now a no-op return.
  - Removed API overwrite assignment in `get_recommendation()` so LLM-selected APIs are preserved.
  - Updated scaffold block text passed to the model to remove forced-choice framing.

- `backend/pipeline/normalizer.py`
  - Removed deterministic overwrites of `constraints`, `input_output`, `data_model`, and `selected_stack`.
  - Kept only structural fallback with empty defaults when fields are missing.

- `backend/pipeline/analyzer.py`
  - Removed stack-based post-LLM filtering/rewrite logic.
  - Removed post-LLM `data_flow` rewriting and `failure_points` stripping.
  - Analyzer now returns LLM output directly (with only missing-field defaults preserved).

- `backend/pipeline/option_advisor.py`
  - Reduced post-processing in `_enforce_option_rules` to type-safety only.
  - Removed score clamping.
  - Removed synthetic `why_not_recommended` generation.
  - Removed synthetic drawbacks injection.

- `backend/pipeline/growth.py`
  - Removed deterministic DB warning injection.
  - Kept consistency checks without forcing extra warning content.

## 2) Before vs after behavior

- Recommender scaffold
  - Before: pre-decided allowed/preferred stack and required APIs.
  - After: neutral scaffold note only; model decides architecture.

- Recommender API list
  - Before: LLM API list could be replaced by deterministic selector output.
  - After: LLM API list is preserved; selector metadata is still attached separately.

- Stack consistency enforcement
  - Before: model stack output could be clamped/replaced.
  - After: model stack output is not altered by enforcement logic.

- Normalizer output shaping
  - Before: core fields were overwritten with templates derived from selected stack.
  - After: no template overwrite; fields come from model output (or empty defaults when missing).

- Analyzer output shaping
  - Before: component/data-flow/failure-point content was modified after LLM response.
  - After: no stack-based content mutation post-LLM.

- Option advisor
  - Before: post-processor could inject reasons/drawbacks and clamp scores.
  - After: post-processor only normalizes types and preserves model intent.

- Growth output
  - Before: DB warnings were injected regardless of model output.
  - After: no forced warning injection.

## 3) Tests modified and why

- No test files were modified.

## 4) Risks introduced

- Lower guardrails can allow invalid or inconsistent stack values from model output.
- Less deterministic post-processing can increase output variability.
- Some downstream assumptions that relied on forced defaults may now surface as missing/weak fields.
