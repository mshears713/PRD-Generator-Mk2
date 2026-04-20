import re


_TRIGGER_PATTERN = re.compile(
    r"(trigger|start|initiat|when .{0,30}(user|client|request)|on (submit|request|call|invoke)|"
    r"user submits|client sends|invoked when|activated by)",
    re.IGNORECASE,
)
_FLOW_PATTERN = re.compile(
    r"(step \d|phase \d|flow|pipeline|sequence|first .{0,20}then|data flow)",
    re.IGNORECASE,
)
_COMPONENT_PATTERN = re.compile(
    r"(component|service|endpoint|layer|module|handler|processor|worker)",
    re.IGNORECASE,
)
_CONSTRAINT_PATTERN = re.compile(
    r"(out of scope|not in scope|excluded|constraint|limitation|does not (support|include|handle)|"
    r"not (supported|included|covered))",
    re.IGNORECASE,
)
_BACKEND_IO_PATTERN = re.compile(
    r"\b(input|output|receive|accept|return|emit|respond)\b",
    re.IGNORECASE,
)
_BACKEND_PROCESSING_PATTERN = re.compile(
    r"\b(process|transform|compute|execut|logic|workflow|validat|calculat|generat|resolv)\b",
    re.IGNORECASE,
)
_BACKEND_PHASES_PATTERN = re.compile(
    r"(phase \d|implementation phase)",
    re.IGNORECASE,
)


def check_prd_quality(main_prd: str, backend_prd: str | None = None) -> dict:
    combined = (main_prd or "") + "\n" + (backend_prd or "")
    warnings = []

    if not _TRIGGER_PATTERN.search(combined):
        warnings.append("No clear execution trigger or system start condition found.")

    if not _FLOW_PATTERN.search(main_prd or ""):
        warnings.append("No clear execution flow found in main PRD.")

    if not _COMPONENT_PATTERN.search(main_prd or ""):
        warnings.append("No key components identified in main PRD.")

    if backend_prd:
        if not _BACKEND_IO_PATTERN.search(backend_prd):
            warnings.append("Backend PRD lacks input/output specification for components.")
        if not _BACKEND_PROCESSING_PATTERN.search(backend_prd):
            warnings.append("Backend PRD lacks processing or transformation details.")
        if not _BACKEND_PHASES_PATTERN.search(backend_prd):
            warnings.append("Backend PRD lacks implementation phases.")

    if not _CONSTRAINT_PATTERN.search(main_prd or ""):
        warnings.append("No explicit constraints or out-of-scope exclusions found in main PRD.")

    passed = len(warnings) == 0
    return {
        "passed": passed,
        "warnings": warnings,
        "summary": "PRD quality check passed." if passed else f"{len(warnings)} quality issue(s) detected.",
    }
