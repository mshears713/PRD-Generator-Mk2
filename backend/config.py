import os
import sys


def _str_to_bool(value: str) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _detect_pytest() -> bool:
    return (
        "PYTEST_CURRENT_TEST" in os.environ
        or os.getenv("PYTEST_RUNNING") == "1"
        or "pytest" in sys.modules
    )


def _resolve_fake_flag() -> bool:
    env_flag = _str_to_bool(os.getenv("USE_FAKE_LLM"))
    if env_flag is not None:
        return env_flag
    return _detect_pytest()


USE_FAKE_LLM = _resolve_fake_flag()


def prd_decomposition_enabled() -> bool:
    env_flag = _str_to_bool(os.getenv("ENABLE_PRD_DECOMPOSITION"))
    if env_flag is not None:
        return env_flag
    return True
