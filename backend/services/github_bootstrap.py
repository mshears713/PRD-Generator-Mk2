from __future__ import annotations

import re


def extract_title_from_markdown(md: str) -> str | None:
    if not md:
        return None
    for line in str(md).splitlines():
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            return title or None
    return None


def slugify_repo_name(text: str) -> str:
    raw = (text or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    if not raw:
        return "stacklens-project"
    if len(raw) > 100:
        raw = raw[:100].rstrip("-")
        raw = raw or "stacklens-project"
    return raw


_REPO_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")


def validate_repo_name_override(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("repo_name cannot be blank")
    candidate = name.strip()
    if not _REPO_NAME_RE.match(candidate):
        raise ValueError(
            "repo_name must be 1-100 chars and start with a letter/number; allowed: letters, numbers, '.', '_', '-'"
        )


def sanitize_env_example(env_text: str | None) -> str:
    if not env_text:
        return (
            "# Copy to .env and fill values\n"
            "OPENAI_API_KEY=\n"
            "GITHUB_TOKEN=\n"
        )

    out_lines: list[str] = []
    for raw_line in str(env_text).splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out_lines.append(line)
            continue
        if "=" not in line:
            out_lines.append(line)
            continue
        key, _value = line.split("=", 1)
        key = key.strip()
        if not key:
            out_lines.append(line)
            continue
        out_lines.append(f"{key}=")
    return "\n".join(out_lines).rstrip() + "\n"


def _seed_backend_main_py() -> str:
    return (
        "from fastapi import FastAPI\n\n"
        "app = FastAPI()\n\n\n"
        "@app.get('/')\n"
        "def root():\n"
        "    return {'ok': True, 'service': 'backend'}\n\n\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'status': 'healthy'}\n"
    )


def _seed_repo_gitignore() -> str:
    return (
        "__pycache__/\n"
        "*.pyc\n"
        "*.pyo\n"
        ".pytest_cache/\n"
        ".venv/\n"
        "venv/\n"
        ".env\n"
        "\n"
    )


def build_scaffold_files(
    *,
    main_prd: str,
    backend_prd: str | None,
    frontend_prd: str | None,
    env_text: str | None,
) -> dict[str, str]:
    files: dict[str, str] = {
        "README.md": main_prd or "",
        "backend_prd.md": backend_prd or "",
        "backend/main.py": _seed_backend_main_py(),
        "backend/requirements.txt": "fastapi\nuvicorn\n",
        ".env.example": sanitize_env_example(env_text),
        ".gitignore": _seed_repo_gitignore(),
    }
    if frontend_prd:
        files["frontend_prd.md"] = frontend_prd
    return files


def build_kickoff_prompt(repo_url: str, has_frontend: bool) -> str:
    doc_lines = [
        "- README.md (main PRD / overview)",
        "- backend_prd.md (backend PRD)",
    ]
    if has_frontend:
        doc_lines.append("- frontend_prd.md (frontend PRD)")

    docs = "\n".join(doc_lines)
    frontend_note = (
        "Implement backend and frontend in small increments."
        if has_frontend
        else "Focus on the backend first; keep the UI minimal unless the PRD requires one."
    )

    return (
        "You are a coding agent helping me build a project scaffolded by StackLens.\n\n"
        f"Repo: {repo_url}\n\n"
        "Source-of-truth docs in this repo:\n"
        f"{docs}\n\n"
        "Constraints:\n"
        "- Keep it simple and reliable; no over-engineering.\n"
        "- Prefer working software first, then polish.\n"
        "- Avoid adding auth/OAuth unless explicitly required by the PRDs.\n\n"
        "Start by reading the docs, then:\n"
        "1) Create a minimal working vertical slice.\n"
        "2) Add endpoints/features one at a time with tests.\n"
        "3) Keep interfaces stable and code explicit.\n\n"
        "Backend quickstart:\n"
        "- cd backend\n"
        "- python -m venv .venv && source .venv/bin/activate\n"
        "- pip install -r requirements.txt\n"
        "- uvicorn main:app --reload\n\n"
        f"{frontend_note}\n"
    )


def next_name_with_suffix(base: str, n: int) -> str:
    suffix = f"-{n}"
    if len(base) + len(suffix) <= 100:
        return f"{base}{suffix}"
    trimmed = base[: 100 - len(suffix)].rstrip("-")
    trimmed = trimmed or "stacklens-project"
    return f"{trimmed}{suffix}"

