# CodeGarden V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack hackathon prototype where users describe an idea, receive a recommended stack, refine it via card UI, then generate a structured PRD, `.env`, and Growth Check.

**Architecture:** FastAPI backend runs a 4-stage LLM pipeline (normalize → analyze → generate PRD → growth check) plus a lightweight `/recommend` endpoint. React + Vite frontend has 3 stages: idea input → recommendation review → output display.

**Tech Stack:** Python 3.10+, FastAPI, OpenAI SDK (gpt-4o), pytest, React 18, Vite, react-markdown

---

## File Map

```
PRD Generator Mk2/
├── backend/
│   ├── main.py                  # FastAPI app — /recommend + /generate endpoints
│   ├── requirements.txt
│   ├── .env.example
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── recommender.py       # /recommend — 1 LLM call: summary + stack
│   │   ├── normalizer.py        # Stage 1 — structured system definition JSON
│   │   ├── analyzer.py          # Stage 2 — components/data_flow/deps/risks JSON
│   │   ├── prd_gen.py           # Stage 3 — PRD markdown
│   │   ├── growth.py            # Stage 4 — Growth Check markdown
│   │   └── env_builder.py       # Stage 5 — deterministic .env string
│   └── tests/
│       ├── __init__.py
│       ├── test_env_builder.py
│       ├── test_recommender.py
│       ├── test_normalizer.py
│       ├── test_analyzer.py
│       ├── test_prd_gen.py
│       ├── test_growth.py
│       └── test_main.py
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── App.jsx              # Root — stage state machine + API calls
        ├── styles/
        │   └── main.css
        └── components/
            ├── IdeaInput.jsx        # Textarea + "Understand My Idea" button
            ├── LoadingState.jsx     # Spinner + rotating stage label
            ├── SelectionCards.jsx   # Card pickers + inline API key inputs
            ├── RecommendationPanel.jsx  # Summary + SelectionCards + Generate button
            └── OutputPanel.jsx      # PRD + .env + Growth Check + Start Over
```

---

## Task 1: Backend Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/pipeline/__init__.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
cd "C:/Users/PC/Desktop/PRD Generator Mk2"
mkdir -p backend/pipeline backend/tests
```

- [ ] **Step 2: Write requirements.txt**

```
fastapi==0.115.6
uvicorn==0.32.1
openai==1.58.1
python-dotenv==1.0.1
pydantic==2.10.3
pytest==8.3.4
httpx==0.28.1
```

Save to `backend/requirements.txt`.

- [ ] **Step 3: Write .env.example**

```
OPENAI_API_KEY=your-openai-key-here
```

Save to `backend/.env.example`. Copy to `backend/.env` and fill in a real key.

- [ ] **Step 4: Create empty __init__ files**

Create empty `backend/pipeline/__init__.py` and `backend/tests/__init__.py`.

- [ ] **Step 5: Install dependencies**

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Expected: All packages install with no errors.

- [ ] **Step 6: Commit**

```bash
git init
git add backend/requirements.txt backend/.env.example backend/pipeline/__init__.py backend/tests/__init__.py
git commit -m "chore: backend project setup"
```

---

## Task 2: env_builder.py (TDD)

**Files:**
- Create: `backend/pipeline/env_builder.py`
- Create: `backend/tests/test_env_builder.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_env_builder.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.env_builder import build_env


def test_always_includes_openai_key():
    result = build_env([], {}, "none")
    assert "OPENAI_API_KEY=" in result


def test_openrouter_key_filled_from_input():
    result = build_env(["openrouter"], {"openrouter": "sk-test-123"}, "none")
    assert "OPENROUTER_API_KEY=sk-test-123" in result


def test_openrouter_key_placeholder_when_not_provided():
    result = build_env(["openrouter"], {}, "none")
    assert "OPENROUTER_API_KEY=your-openrouter-key-here" in result


def test_tavily_key_filled_from_input():
    result = build_env(["tavily"], {"tavily": "tvly-abc"}, "none")
    assert "TAVILY_API_KEY=tvly-abc" in result


def test_postgres_adds_database_url():
    result = build_env([], {}, "postgres")
    assert "DATABASE_URL=" in result
    assert "postgres://" in result


def test_firebase_adds_multiple_keys():
    result = build_env([], {}, "firebase")
    assert "FIREBASE_PROJECT_ID=" in result
    assert "FIREBASE_API_KEY=" in result


def test_no_db_no_database_keys():
    result = build_env([], {}, "none")
    assert "DATABASE_URL" not in result
    assert "FIREBASE" not in result


def test_multiple_apis_and_db():
    result = build_env(["openrouter", "tavily"], {"openrouter": "sk-or"}, "postgres")
    assert "OPENROUTER_API_KEY=sk-or" in result
    assert "TAVILY_API_KEY=your-tavily-key-here" in result
    assert "DATABASE_URL=" in result


def test_result_is_string():
    result = build_env(["openrouter"], {}, "postgres")
    assert isinstance(result, str)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend
pytest tests/test_env_builder.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (file doesn't exist yet).

- [ ] **Step 3: Implement env_builder.py**

Save as `backend/pipeline/env_builder.py`:

```python
def build_env(apis: list[str], api_keys: dict[str, str], database: str) -> str:
    API_KEY_MAP = {
        "openrouter": ("OPENROUTER_API_KEY", "OpenRouter API key for LLM routing"),
        "tavily": ("TAVILY_API_KEY", "Tavily search API key"),
    }

    DB_MAP = {
        "postgres": [
            ("DATABASE_URL", "postgres://user:pass@localhost:5432/dbname", "PostgreSQL connection string [REQUIRED]"),
        ],
        "firebase": [
            ("FIREBASE_PROJECT_ID", "", "Firebase project ID [REQUIRED]"),
            ("FIREBASE_API_KEY", "", "Firebase web API key [REQUIRED]"),
            ("FIREBASE_AUTH_DOMAIN", "", "Firebase auth domain [OPTIONAL]"),
        ],
    }

    lines = [
        "# .env — Generated by CodeGarden",
        "# REQUIRED keys must be set before running. OPTIONAL keys can be left empty.",
        "",
        "# CodeGarden backend [REQUIRED]",
        "OPENAI_API_KEY=your-openai-key-here",
        "",
    ]

    if apis:
        lines.append("# External APIs")
        for api in apis:
            if api in API_KEY_MAP:
                key_name, comment = API_KEY_MAP[api]
                value = api_keys.get(api, f"your-{api}-key-here")
                lines.append(f"# {comment} [REQUIRED]")
                lines.append(f"{key_name}={value}")
                lines.append("")

    if database in DB_MAP:
        lines.append("# Database")
        for key_name, default, comment in DB_MAP[database]:
            value = default if default else f"your-{key_name.lower()}-here"
            lines.append(f"# {comment}")
            lines.append(f"{key_name}={value}")
            lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_env_builder.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/env_builder.py backend/tests/test_env_builder.py
git commit -m "feat: deterministic env_builder with tests"
```

---

## Task 3: recommender.py (TDD)

**Files:**
- Create: `backend/pipeline/recommender.py`
- Create: `backend/tests/test_recommender.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_recommender.py`:

```python
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.recommender import get_recommendation


FAKE_RESPONSE = {
    "summary": "A task management platform where remote teams create, assign, and track tasks in real time.",
    "recommended": {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": [],
        "database": "postgres",
    },
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_returns_summary_and_recommended():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("A task manager for remote teams")
    assert "summary" in result
    assert "recommended" in result


def test_recommended_has_required_keys():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    rec = result["recommended"]
    assert "scope" in rec
    assert "backend" in rec
    assert "frontend" in rec
    assert "apis" in rec
    assert "database" in rec


def test_apis_is_list():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert isinstance(result["recommended"]["apis"], list)


def test_summary_is_nonempty_string():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_recommender.py -v
```

Expected: `ImportError` (file doesn't exist).

- [ ] **Step 3: Implement recommender.py**

Save as `backend/pipeline/recommender.py`:

```python
import json
import os
from openai import OpenAI


def get_recommendation(idea: str) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architecture advisor. Given a raw idea, analyze it and output JSON.\n\n"
                    "Output this exact structure:\n"
                    "{\n"
                    '  "summary": "1-2 sentence plain-language description of what the system does",\n'
                    '  "recommended": {\n'
                    '    "scope": "fullstack",\n'
                    '    "backend": "fastapi",\n'
                    '    "frontend": "react",\n'
                    '    "apis": [],\n'
                    '    "database": "postgres"\n'
                    "  }\n"
                    "}\n\n"
                    "Rules:\n"
                    "- scope: one of: frontend, backend, fullstack\n"
                    "- backend: one of: fastapi, node, none\n"
                    "- frontend: one of: react, static, none\n"
                    "- apis: array, elements must be from: openrouter, tavily — only include if clearly needed\n"
                    "- database: one of: postgres, firebase, none\n"
                    "- Default to fullstack + fastapi + react + postgres for most web app ideas.\n"
                    "- Only include openrouter if the app clearly needs LLM/AI features.\n"
                    "- Only include tavily if the app clearly needs web search.\n"
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": f"Idea: {idea}"},
        ],
    )

    return json.loads(response.choices[0].message.content)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_recommender.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/recommender.py backend/tests/test_recommender.py
git commit -m "feat: recommender pipeline stage with tests"
```

---

## Task 4: normalizer.py (TDD)

**Files:**
- Create: `backend/pipeline/normalizer.py`
- Create: `backend/tests/test_normalizer.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_normalizer.py`:

```python
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.normalizer import normalize


FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams create, assign, and track tasks with real-time updates.",
    "core_features": ["Create tasks", "Assign to users", "Track status", "Real-time updates"],
    "user_types": ["admin", "team member"],
    "constraints": ["FastAPI backend requires Python 3.10+", "React frontend requires Node 18+"],
    "assumptions_removed": ["'real-time' → WebSocket-based live updates", "'remote teams' → multi-user with role-based access"],
}

SELECTIONS = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": [],
    "database": "postgres",
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_normalize_returns_required_keys():
    with patch("pipeline.normalizer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_NORMALIZED)
        result = normalize("A task manager for remote teams", SELECTIONS)
    for key in ["system_name", "purpose", "core_features", "user_types", "constraints", "assumptions_removed"]:
        assert key in result, f"Missing key: {key}"


def test_core_features_is_list():
    with patch("pipeline.normalizer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_NORMALIZED)
        result = normalize("anything", SELECTIONS)
    assert isinstance(result["core_features"], list)
    assert len(result["core_features"]) >= 1


def test_purpose_is_nonempty_string():
    with patch("pipeline.normalizer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_NORMALIZED)
        result = normalize("anything", SELECTIONS)
    assert isinstance(result["purpose"], str)
    assert len(result["purpose"]) > 10
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_normalizer.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement normalizer.py**

Save as `backend/pipeline/normalizer.py`:

```python
import json
import os
from openai import OpenAI


def normalize(idea: str, selections: dict) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software requirements analyst. Remove vagueness from a product idea "
                    "and produce a clear, unambiguous system definition.\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  "system_name": "Short descriptive name (2-4 words, title case)",\n'
                    '  "purpose": "One precise sentence: what the system does and for whom",\n'
                    '  "core_features": ["concrete feature 1", "concrete feature 2", "..."],\n'
                    '  "user_types": ["user role 1", "user role 2"],\n'
                    '  "constraints": ["technical constraint from stack"],\n'
                    '  "assumptions_removed": ["vague phrase → specific replacement"]\n'
                    "}\n\n"
                    "Rules:\n"
                    "- purpose: specific (bad: 'helps users'; good: 'lets remote teams create, assign, and track tasks with real-time updates')\n"
                    "- core_features: 4-6 items, each a concrete capability\n"
                    "- constraints: derive from the stack (e.g. 'FastAPI backend requires Python 3.10+')\n"
                    "- assumptions_removed: min 2 items showing how you clarified vague language\n"
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": f"Idea: {idea}\nStack: {stack_desc}"},
        ],
    )

    return json.loads(response.choices[0].message.content)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_normalizer.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/normalizer.py backend/tests/test_normalizer.py
git commit -m "feat: normalizer pipeline stage with tests"
```

---

## Task 5: analyzer.py (TDD)

**Files:**
- Create: `backend/pipeline/analyzer.py`
- Create: `backend/tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_analyzer.py`:

```python
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.analyzer import analyze


FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions_removed": ["vague → specific"],
}

FAKE_ARCHITECTURE = {
    "components": [
        {"name": "Task API", "responsibility": "CRUD operations for tasks"},
        {"name": "Auth Service", "responsibility": "User authentication and sessions"},
    ],
    "data_flow": [
        "Step 1: User submits task → API validates and stores in DB",
        "Step 2: Assigned user notified via WebSocket",
    ],
    "dependencies": [
        "Task API depends on Auth Service for user identity"
    ],
    "risks": [
        "WebSocket connections may not scale without a message broker"
    ],
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_analyze_returns_required_keys():
    with patch("pipeline.analyzer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ARCHITECTURE)
        result = analyze(FAKE_NORMALIZED)
    for key in ["components", "data_flow", "dependencies", "risks"]:
        assert key in result, f"Missing key: {key}"


def test_components_are_list_of_dicts():
    with patch("pipeline.analyzer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ARCHITECTURE)
        result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["components"], list)
    assert len(result["components"]) >= 1
    assert "name" in result["components"][0]
    assert "responsibility" in result["components"][0]


def test_data_flow_is_list_of_strings():
    with patch("pipeline.analyzer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ARCHITECTURE)
        result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["data_flow"], list)
    assert all(isinstance(s, str) for s in result["data_flow"])
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_analyzer.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement analyzer.py**

Save as `backend/pipeline/analyzer.py`:

```python
import json
import os
from openai import OpenAI


def analyze(normalized: dict) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architect. Given a normalized system definition, produce a concrete architecture analysis.\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  "components": [\n'
                    '    {"name": "Component Name", "responsibility": "What it does in one sentence"}\n'
                    "  ],\n"
                    '  "data_flow": [\n'
                    '    "Step 1: User does X → Y happens",\n'
                    '    "Step 2: ..."\n'
                    "  ],\n"
                    '  "dependencies": [\n'
                    '    "Component A calls Component B for X"\n'
                    "  ],\n"
                    '  "risks": [\n'
                    '    "Risk description and why it matters"\n'
                    "  ]\n"
                    "}\n\n"
                    "Rules:\n"
                    "- components: 4-8 items, each with a single clear responsibility\n"
                    "- data_flow: 3-6 steps showing how data moves for the primary use case\n"
                    "- dependencies: list all non-obvious inter-component dependencies\n"
                    "- risks: 2-4 realistic technical risks specific to this system\n"
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": f"System definition:\n{json.dumps(normalized, indent=2)}"},
        ],
    )

    return json.loads(response.choices[0].message.content)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_analyzer.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/analyzer.py backend/tests/test_analyzer.py
git commit -m "feat: architecture analyzer pipeline stage with tests"
```

---

## Task 6: prd_gen.py (TDD)

**Files:**
- Create: `backend/pipeline/prd_gen.py`
- Create: `backend/tests/test_prd_gen.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_prd_gen.py`:

```python
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.prd_gen import generate_prd


FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions_removed": ["vague → specific"],
}

FAKE_ARCHITECTURE = {
    "components": [{"name": "Task API", "responsibility": "CRUD for tasks"}],
    "data_flow": ["Step 1: User creates task → stored in DB"],
    "dependencies": ["Task API uses DB"],
    "risks": ["No rate limiting on API"],
}

FAKE_PRD = """# TeamTask PRD

## Overview
TeamTask helps remote teams track work.

## Architecture
FastAPI backend with React frontend.

## Components
### Task API
- **Responsibility:** CRUD operations for tasks

## API Usage
No external APIs required.

## Database Design
tasks table: id, title, assigned_to, status, created_at

## Test Cases
| Test | Input | Expected Output | Type |
|------|-------|-----------------|------|
| Create task | POST /tasks with title | 201 + task JSON | integration |
"""


def make_openai_response(content: str):
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


def test_generate_prd_returns_string():
    with patch("pipeline.prd_gen.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_PRD)
        result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    assert isinstance(result, str)
    assert len(result) > 100


def test_generate_prd_contains_required_sections():
    with patch("pipeline.prd_gen.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_PRD)
        result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    for section in ["Overview", "Architecture", "Components", "Test Cases"]:
        assert section in result, f"Missing section: {section}"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_prd_gen.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement prd_gen.py**

Save as `backend/pipeline/prd_gen.py`:

```python
import json
import os
from openai import OpenAI


def generate_prd(normalized: dict, architecture: dict) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior technical writer producing agent-ready PRDs. "
                    "Given a system definition and architecture analysis, write a structured PRD in markdown.\n\n"
                    "The PRD must have exactly these sections in this order:\n\n"
                    "# [System Name] PRD\n\n"
                    "## Overview\n"
                    "(2-3 sentences: purpose, users, core value)\n\n"
                    "## Architecture\n"
                    "(Describe the overall system structure, key design decisions, and how components interact. 3-5 sentences.)\n\n"
                    "## Components\n"
                    "(For each component, one subsection:)\n"
                    "### [Component Name]\n"
                    "- **Responsibility:** ...\n"
                    "- **Interface:** how other parts interact with it\n"
                    "- **Key logic:** what it actually does\n\n"
                    "## API Usage\n"
                    "(If external APIs are used, describe how each is used, data in/out, rate limit concerns. "
                    "If no APIs, write 'No external APIs required.')\n\n"
                    "## Database Design\n"
                    "(Table/collection names, key fields, relationships. "
                    "If no database, write 'No persistent storage required.')\n\n"
                    "## Test Cases\n"
                    "(Minimum 6 test cases covering happy path and edge cases.)\n"
                    "| Test | Input | Expected Output | Type |\n"
                    "|------|-------|-----------------|------|\n"
                    "| ... | ... | ... | unit/integration/e2e |\n\n"
                    "Output ONLY the markdown. No preamble, no closing remarks."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"System definition:\n{json.dumps(normalized, indent=2)}\n\n"
                    f"Architecture:\n{json.dumps(architecture, indent=2)}"
                ),
            },
        ],
    )

    return response.choices[0].message.content
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_prd_gen.py -v
```

Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/prd_gen.py backend/tests/test_prd_gen.py
git commit -m "feat: PRD generator pipeline stage with tests"
```

---

## Task 7: growth.py (TDD)

**Files:**
- Create: `backend/pipeline/growth.py`
- Create: `backend/tests/test_growth.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_growth.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.growth import generate_growth_check


FAKE_PRD = "# TeamTask PRD\n## Overview\nA task manager.\n## Test Cases\n| Test | Input | Expected | Type |\n|------|-------|----------|------|\n| create | POST | 201 | integration |"

SELECTIONS = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": [],
    "database": "postgres",
}

FAKE_GROWTH = """## Growth Check

### ✅ Good Choices
- **FastAPI + React:** Proven fullstack combination with strong ecosystem support.
- **PostgreSQL:** Reliable relational database well-suited for task management data.

### ⚠️ Warnings
- **No authentication:** The PRD does not define an auth mechanism — tasks will be publicly writable.

### ❌ Missing Components
- **Rate limiting:** No rate limiting on the API means the endpoint is open to abuse.
"""


def make_openai_response(content: str):
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


def test_growth_check_returns_string():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check(FAKE_PRD, SELECTIONS)
    assert isinstance(result, str)
    assert len(result) > 50


def test_growth_check_contains_indicators():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check(FAKE_PRD, SELECTIONS)
    assert "✅" in result
    assert "⚠️" in result
    assert "❌" in result
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_growth.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement growth.py**

Save as `backend/pipeline/growth.py`:

```python
import os
from openai import OpenAI


def generate_growth_check(prd: str, selections: dict) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software architect reviewing a project blueprint. "
                    "Produce a Growth Check — a concise, honest evaluation of the stack and design choices.\n\n"
                    "Format your output in markdown exactly like this:\n\n"
                    "## Growth Check\n\n"
                    "### ✅ Good Choices\n"
                    "- **[Choice]:** [Why it's a good fit for this specific system]\n"
                    "(2-4 items)\n\n"
                    "### ⚠️ Warnings\n"
                    "- **[Concern]:** [What could go wrong and why]\n"
                    "(1-3 items)\n\n"
                    "### ❌ Missing Components\n"
                    "- **[Missing thing]:** [What it is and why this system needs it]\n"
                    "(1-3 items — only flag genuinely missing pieces, not nice-to-haves)\n\n"
                    "Rules:\n"
                    "- Be specific to THIS system, not generic advice\n"
                    "- ✅ items explain WHY this choice fits (not just 'FastAPI is fast')\n"
                    "- ⚠️ items name concrete failure modes\n"
                    "- ❌ items flag things actually missing (auth if users exist, rate limiting if external APIs used)\n"
                    "- Output ONLY the markdown. No preamble."
                ),
            },
            {
                "role": "user",
                "content": f"Stack selections: {stack_desc}\n\nPRD:\n{prd}",
            },
        ],
    )

    return response.choices[0].message.content
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_growth.py -v
```

Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/growth.py backend/tests/test_growth.py
git commit -m "feat: growth check pipeline stage with tests"
```

---

## Task 8: main.py — Wire Everything Together (TDD)

**Files:**
- Create: `backend/main.py`
- Create: `backend/tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Save as `backend/tests/test_main.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from fastapi.testclient import TestClient


FAKE_RECOMMENDATION = {
    "summary": "A task manager for remote teams.",
    "recommended": {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": [],
        "database": "postgres",
    },
}

GENERATE_PAYLOAD = {
    "idea": "A task manager for remote teams",
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": ["openrouter"],
    "database": "postgres",
    "api_keys": {"openrouter": "sk-test"},
}


def get_client():
    # Import inside function so env var is set first
    os.environ["OPENAI_API_KEY"] = "test-key"
    from main import app
    return TestClient(app)


def test_recommend_returns_200():
    with patch("main.get_recommendation", return_value=FAKE_RECOMMENDATION):
        client = get_client()
        response = client.post("/recommend", json={"idea": "A task manager"})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recommended" in data


def test_generate_returns_200():
    with (
        patch("main.normalize", return_value={"system_name": "TeamTask", "purpose": "test"}),
        patch("main.analyze", return_value={"components": [], "data_flow": [], "dependencies": [], "risks": []}),
        patch("main.generate_prd", return_value="# PRD\n## Overview\ntest\n## Test Cases\n"),
        patch("main.generate_growth_check", return_value="## Growth Check\n✅ good\n⚠️ warn\n❌ missing"),
    ):
        client = get_client()
        response = client.post("/generate", json=GENERATE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "prd" in data
    assert "env" in data
    assert "growth_check" in data


def test_generate_env_contains_openrouter_key():
    with (
        patch("main.normalize", return_value={}),
        patch("main.analyze", return_value={}),
        patch("main.generate_prd", return_value="# PRD"),
        patch("main.generate_growth_check", return_value="## Growth Check\n✅ good"),
    ):
        client = get_client()
        response = client.post("/generate", json=GENERATE_PAYLOAD)
    assert "OPENROUTER_API_KEY=sk-test" in response.json()["env"]


def test_recommend_missing_openai_key_returns_500():
    os.environ.pop("OPENAI_API_KEY", None)
    from importlib import reload
    import main as m
    reload(m)
    client = TestClient(m.app)
    response = client.post("/recommend", json={"idea": "test"})
    assert response.status_code == 500
    os.environ["OPENAI_API_KEY"] = "test-key"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError` (main.py doesn't exist).

- [ ] **Step 3: Implement main.py**

Save as `backend/main.py`:

```python
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from pipeline.recommender import get_recommendation
from pipeline.normalizer import normalize
from pipeline.analyzer import analyze
from pipeline.prd_gen import generate_prd
from pipeline.growth import generate_growth_check
from pipeline.env_builder import build_env

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    idea: str


class GenerateRequest(BaseModel):
    idea: str
    scope: str
    backend: str
    frontend: str
    apis: list[str] = []
    database: str
    api_keys: dict[str, str] = {}


@app.post("/recommend")
def recommend(req: RecommendRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    return get_recommendation(req.idea)


@app.post("/generate")
def generate(req: GenerateRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    selections = {
        "scope": req.scope,
        "backend": req.backend,
        "frontend": req.frontend,
        "apis": req.apis,
        "database": req.database,
    }

    normalized = normalize(req.idea, selections)
    architecture = analyze(normalized)
    prd = generate_prd(normalized, architecture)
    growth_check = generate_growth_check(prd, selections)
    env = build_env(req.apis, req.api_keys, req.database)

    return {"prd": prd, "env": env, "growth_check": growth_check}
```

- [ ] **Step 4: Run all backend tests**

```bash
pytest tests/ -v
```

Expected: All tests PASS. Note the `test_recommend_missing_openai_key_returns_500` test uses module reload — if it's flaky, run it in isolation: `pytest tests/test_main.py::test_recommend_missing_openai_key_returns_500 -v`.

- [ ] **Step 5: Smoke test the running server**

```bash
uvicorn main:app --reload --port 8000
```

In a second terminal:
```bash
curl -X POST http://localhost:8000/recommend -H "Content-Type: application/json" -d "{\"idea\": \"A task manager for remote teams\"}"
```

Expected: JSON with `summary` and `recommended` keys (real LLM response, takes ~3s).

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_main.py
git commit -m "feat: wire pipeline into FastAPI endpoints with integration tests"
```

---

## Task 9: Frontend Scaffold + Styles

**Files:**
- Create: `frontend/` (via Vite)
- Create: `frontend/vite.config.js`
- Create: `frontend/src/styles/main.css`

- [ ] **Step 1: Scaffold Vite React project**

```bash
cd "C:/Users/PC/Desktop/PRD Generator Mk2"
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-markdown
```

- [ ] **Step 2: Clean up Vite boilerplate**

Delete these files (Vite creates them, we don't need them):
- `frontend/src/App.css`
- `frontend/src/assets/react.svg`
- `frontend/public/vite.svg`

Edit `frontend/index.html` — replace the `<title>` content with `CodeGarden`:
```html
<title>CodeGarden</title>
```

- [ ] **Step 3: Write vite.config.js**

Replace contents of `frontend/vite.config.js`:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/recommend': 'http://localhost:8000',
      '/generate': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 4: Write main.css**

Create `frontend/src/styles/main.css`:

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0f0f11;
  --surface: #1a1a1f;
  --border: #2a2a32;
  --accent: #7c6cf0;
  --accent-hover: #6b5ce0;
  --text: #e8e8f0;
  --text-muted: #888898;
  --danger: #f87171;
  --radius: 8px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  min-height: 100vh;
  line-height: 1.6;
}

.app {
  max-width: 760px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}

.app-header { text-align: center; margin-bottom: 3rem; }

.app-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-tagline { color: var(--text-muted); margin-top: 0.4rem; font-size: 1rem; }

.error-banner {
  background: rgba(248, 113, 113, 0.12);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

/* Buttons */
.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  width: 100%;
  margin-top: 1rem;
}
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  padding: 0.65rem 1.25rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.btn-secondary:hover { border-color: var(--text-muted); color: var(--text); }

/* Idea stage */
.idea-stage { display: flex; justify-content: center; }
.idea-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 2rem;
  width: 100%;
}
.idea-label { display: block; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.75rem; }
.idea-textarea {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-family: var(--font);
  font-size: 0.95rem;
  padding: 0.75rem;
  resize: vertical;
  transition: border-color 0.15s;
}
.idea-textarea:focus { outline: none; border-color: var(--accent); }
.idea-hint { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.4rem; }

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 0;
  gap: 1rem;
}
.spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-message { color: var(--text-muted); font-size: 0.95rem; }

/* Recommendation stage */
.recommendation-stage { display: flex; flex-direction: column; gap: 2rem; }
.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}
.summary-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent);
  margin-bottom: 0.5rem;
}
.summary-text { color: var(--text); font-size: 1rem; }

.section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; }
.editable-note { color: var(--text-muted); font-weight: 400; font-size: 0.82rem; }

/* Selection Cards */
.selection-cards { display: flex; flex-direction: column; gap: 1.5rem; }
.card-group-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.card-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.card-btn {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.88rem;
  cursor: pointer;
  transition: all 0.15s;
  text-transform: capitalize;
}
.card-btn:hover { border-color: var(--accent); color: var(--text); }
.card-btn.selected {
  background: rgba(124, 108, 240, 0.15);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.api-key-input { margin-top: 0.75rem; display: flex; flex-direction: column; gap: 0.3rem; }
.api-key-input label { font-size: 0.78rem; color: var(--text-muted); text-transform: capitalize; }
.api-key-input input {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-family: monospace;
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  transition: border-color 0.15s;
  max-width: 400px;
}
.api-key-input input:focus { outline: none; border-color: var(--accent); }

/* Output stage */
.output-stage { display: flex; flex-direction: column; gap: 2rem; }
.output-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}
.output-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.output-section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; }
.output-section-header .output-section-title { margin-bottom: 0; }
.copy-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.3rem 0.75rem;
  border-radius: var(--radius);
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
}
.copy-btn:hover { border-color: var(--accent); color: var(--accent); }
.env-block {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  font-family: monospace;
  font-size: 0.82rem;
  white-space: pre-wrap;
  color: var(--text);
  overflow-x: auto;
}
.start-over-row { display: flex; justify-content: center; }

/* Markdown */
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  color: var(--text);
  font-weight: 600;
  margin: 1rem 0 0.5rem;
}
.markdown-body h1 { font-size: 1.35rem; }
.markdown-body h2 {
  font-size: 1.05rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.25rem;
}
.markdown-body h3 { font-size: 0.95rem; }
.markdown-body p { margin: 0.5rem 0; }
.markdown-body ul, .markdown-body ol { padding-left: 1.5rem; margin: 0.4rem 0; }
.markdown-body li { margin: 0.2rem 0; }
.markdown-body table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.83rem; }
.markdown-body th, .markdown-body td {
  border: 1px solid var(--border);
  padding: 0.4rem 0.75rem;
  text-align: left;
}
.markdown-body th { background: var(--bg); font-weight: 600; }
.markdown-body code {
  background: var(--bg);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.84em;
  font-family: monospace;
}
.markdown-body pre {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}
.markdown-body pre code { background: none; padding: 0; }
.markdown-body strong { font-weight: 600; }
```

- [ ] **Step 5: Verify dev server starts**

```bash
npm run dev
```

Expected: Vite starts on `http://localhost:5173`. Opening in browser shows Vite's default React page (we haven't built our components yet).

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold with Vite, React, styles"
```

---

## Task 10: IdeaInput.jsx + LoadingState.jsx + App.jsx skeleton

**Files:**
- Create: `frontend/src/components/IdeaInput.jsx`
- Create: `frontend/src/components/LoadingState.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/main.jsx`

- [ ] **Step 1: Write IdeaInput.jsx**

Save as `frontend/src/components/IdeaInput.jsx`:

```jsx
export default function IdeaInput({ idea, onChange, onSubmit }) {
  function handleKey(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') onSubmit()
  }

  return (
    <div className="idea-stage">
      <div className="idea-card">
        <label className="idea-label">Describe your idea</label>
        <textarea
          className="idea-textarea"
          placeholder="e.g. A task manager for remote teams with real-time updates and role-based access..."
          value={idea}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKey}
          rows={5}
          autoFocus
        />
        <p className="idea-hint">Tip: Ctrl+Enter to submit</p>
        <button
          className="btn-primary"
          onClick={onSubmit}
          disabled={!idea.trim()}
        >
          Understand My Idea →
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Write LoadingState.jsx**

Save as `frontend/src/components/LoadingState.jsx`:

```jsx
import { useState, useEffect } from 'react'

export default function LoadingState({ message, stages, cycleInterval = 6000 }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!stages) return
    const timer = setInterval(
      () => setIndex(i => Math.min(i + 1, stages.length - 1)),
      cycleInterval
    )
    return () => clearInterval(timer)
  }, [stages, cycleInterval])

  return (
    <div className="loading-state">
      <div className="spinner" />
      <p className="loading-message">{stages ? stages[index] : message}</p>
    </div>
  )
}
```

- [ ] **Step 3: Write App.jsx skeleton (idea stage only)**

Save as `frontend/src/App.jsx`:

```jsx
import { useState } from 'react'
import IdeaInput from './components/IdeaInput'
import LoadingState from './components/LoadingState'
import './styles/main.css'

const GENERATE_STAGES = [
  'Normalizing system definition...',
  'Analyzing architecture...',
  'Generating PRD...',
  'Running Growth Check...',
]

export default function App() {
  const [stage, setStage] = useState('idea')
  const [idea, setIdea] = useState('')
  const [summary, setSummary] = useState('')
  const [recommended, setRecommended] = useState(null)
  const [selections, setSelections] = useState({
    scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {},
  })
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')

  async function handleUnderstand() {
    if (!idea.trim()) return
    setStage('recommending')
    setError('')
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setSummary(data.summary)
      setRecommended(data.recommended)
      setSelections({ ...data.recommended, api_keys: {} })
      setStage('recommendation')
    } catch (e) {
      setError(e.message)
      setStage('idea')
    }
  }

  async function handleGenerate() {
    setStage('generating')
    setError('')
    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, ...selections }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setOutput(data)
      setStage('output')
    } catch (e) {
      setError(e.message)
      setStage('recommendation')
    }
  }

  function handleReset() {
    setStage('idea')
    setIdea('')
    setSummary('')
    setRecommended(null)
    setSelections({ scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {} })
    setOutput(null)
    setError('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>CodeGarden</h1>
        <p className="app-tagline">Grow your idea into a build-ready blueprint</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {stage === 'idea' && (
        <IdeaInput idea={idea} onChange={setIdea} onSubmit={handleUnderstand} />
      )}
      {stage === 'recommending' && (
        <LoadingState message="Understanding your idea..." />
      )}
      {/* recommendation, generating, output — added in later tasks */}
      {stage === 'generating' && (
        <LoadingState stages={GENERATE_STAGES} cycleInterval={6000} />
      )}
    </div>
  )
}
```

- [ ] **Step 4: Fix main.jsx import**

Replace contents of `frontend/src/main.jsx`:

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 5: Verify in browser**

With both backend and frontend running, open `http://localhost:5173`. You should see:
- "CodeGarden" gradient heading
- "Describe your idea" textarea
- "Understand My Idea →" button (disabled when empty)
- Typing in textarea enables the button

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: idea input stage + loading state components"
```

---

## Task 11: SelectionCards.jsx

**Files:**
- Create: `frontend/src/components/SelectionCards.jsx`

- [ ] **Step 1: Write SelectionCards.jsx**

Save as `frontend/src/components/SelectionCards.jsx`:

```jsx
const OPTIONS = {
  scope: ['frontend', 'backend', 'fullstack'],
  backend: ['fastapi', 'node', 'none'],
  frontend: ['react', 'static', 'none'],
  apis: ['openrouter', 'tavily'],
  database: ['postgres', 'firebase', 'none'],
}

const LABELS = {
  scope: 'Scope',
  backend: 'Backend',
  frontend: 'Frontend',
  apis: 'APIs (multi-select)',
  database: 'Database',
}

export default function SelectionCards({ selections, onChange }) {
  function selectSingle(field, value) {
    onChange({ ...selections, [field]: value })
  }

  function toggleApi(api) {
    const current = selections.apis || []
    const next = current.includes(api)
      ? current.filter(a => a !== api)
      : [...current, api]
    const api_keys = { ...selections.api_keys }
    if (!next.includes(api)) delete api_keys[api]
    onChange({ ...selections, apis: next, api_keys })
  }

  function setApiKey(api, value) {
    onChange({ ...selections, api_keys: { ...selections.api_keys, [api]: value } })
  }

  return (
    <div className="selection-cards">
      {['scope', 'backend', 'frontend'].map(field => (
        <div className="card-group" key={field}>
          <label className="card-group-label">{LABELS[field]}</label>
          <div className="card-row">
            {OPTIONS[field].map(opt => (
              <button
                key={opt}
                className={`card-btn${selections[field] === opt ? ' selected' : ''}`}
                onClick={() => selectSingle(field, opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}

      <div className="card-group">
        <label className="card-group-label">{LABELS.apis}</label>
        <div className="card-row">
          {OPTIONS.apis.map(api => (
            <button
              key={api}
              className={`card-btn${(selections.apis || []).includes(api) ? ' selected' : ''}`}
              onClick={() => toggleApi(api)}
            >
              {api}
            </button>
          ))}
        </div>
        {(selections.apis || []).map(api => (
          <div className="api-key-input" key={api}>
            <label>{api} API key</label>
            <input
              type="text"
              placeholder={`Enter your ${api} key...`}
              value={selections.api_keys?.[api] || ''}
              onChange={e => setApiKey(api, e.target.value)}
            />
          </div>
        ))}
      </div>

      <div className="card-group">
        <label className="card-group-label">{LABELS.database}</label>
        <div className="card-row">
          {OPTIONS.database.map(opt => (
            <button
              key={opt}
              className={`card-btn${selections.database === opt ? ' selected' : ''}`}
              onClick={() => selectSingle('database', opt)}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify visually (no wiring yet)**

No direct way to see this until RecommendationPanel is built. Move to next task.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SelectionCards.jsx
git commit -m "feat: SelectionCards component with multi-select API support"
```

---

## Task 12: RecommendationPanel.jsx + wire into App.jsx

**Files:**
- Create: `frontend/src/components/RecommendationPanel.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Write RecommendationPanel.jsx**

Save as `frontend/src/components/RecommendationPanel.jsx`:

```jsx
import SelectionCards from './SelectionCards'

export default function RecommendationPanel({ summary, selections, onChange, onGenerate }) {
  const canGenerate = Boolean(
    selections.scope && selections.backend && selections.frontend && selections.database
  )

  return (
    <div className="recommendation-stage">
      <div className="summary-card">
        <p className="summary-label">System Understanding</p>
        <p className="summary-text">{summary}</p>
      </div>

      <div>
        <h2 className="section-title">
          Recommended Setup{' '}
          <span className="editable-note">(fully editable)</span>
        </h2>
        <SelectionCards selections={selections} onChange={onChange} />
      </div>

      <button
        className="btn-primary"
        onClick={onGenerate}
        disabled={!canGenerate}
      >
        Generate Blueprint →
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Add RecommendationPanel to App.jsx**

In `frontend/src/App.jsx`, add the import at the top:

```jsx
import RecommendationPanel from './components/RecommendationPanel'
```

Then add the recommendation stage render. In the JSX return, after the `stage === 'recommending'` block and before `stage === 'generating'`, add:

```jsx
{stage === 'recommendation' && (
  <RecommendationPanel
    summary={summary}
    selections={selections}
    onChange={setSelections}
    onGenerate={handleGenerate}
  />
)}
```

- [ ] **Step 3: Verify end-to-end flow (idea → recommendation)**

With backend running: enter an idea, click "Understand My Idea →". Verify:
- Spinner shows "Understanding your idea..."
- Summary paragraph appears
- Cards are pre-selected with recommended values
- Clicking a card changes the selection
- Clicking an API card reveals the key input
- "Generate Blueprint →" is enabled when all required fields are filled

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/RecommendationPanel.jsx frontend/src/App.jsx
git commit -m "feat: recommendation panel with pre-filled editable card selections"
```

---

## Task 13: OutputPanel.jsx + wire into App.jsx

**Files:**
- Create: `frontend/src/components/OutputPanel.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Write OutputPanel.jsx**

Save as `frontend/src/components/OutputPanel.jsx`:

```jsx
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button className="copy-btn" onClick={copy}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

export default function OutputPanel({ output, onReset }) {
  return (
    <div className="output-stage">
      <div className="output-section">
        <h2 className="output-section-title">PRD</h2>
        <div className="markdown-body">
          <ReactMarkdown>{output.prd}</ReactMarkdown>
        </div>
      </div>

      <div className="output-section">
        <div className="output-section-header">
          <h2 className="output-section-title">.env</h2>
          <CopyButton text={output.env} />
        </div>
        <pre className="env-block">{output.env}</pre>
      </div>

      <div className="output-section">
        <h2 className="output-section-title">Growth Check</h2>
        <div className="markdown-body">
          <ReactMarkdown>{output.growth_check}</ReactMarkdown>
        </div>
      </div>

      <div className="start-over-row">
        <button className="btn-secondary" onClick={onReset}>← Start Over</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add OutputPanel to App.jsx**

In `frontend/src/App.jsx`, add the import:

```jsx
import OutputPanel from './components/OutputPanel'
```

Add the output stage render at the end of the JSX return (after the generating block):

```jsx
{stage === 'output' && (
  <OutputPanel output={output} onReset={handleReset} />
)}
```

- [ ] **Step 3: Full end-to-end verification**

With both servers running, complete the full flow:
1. Enter idea: "A recipe sharing app where users can post, rate, and save recipes"
2. Click "Understand My Idea →" — spinner, then recommendation appears
3. Note recommended stack. Change one card (e.g., add OpenRouter API, enter any fake key)
4. Click "Generate Blueprint →" — generating spinner cycles through 4 labels
5. Output appears. Verify:
   - PRD renders as formatted markdown with Overview, Architecture, Components, API Usage, Database Design, Test Cases sections
   - `.env` block shows the correct keys (OPENROUTER_API_KEY filled with fake key, DATABASE_URL if postgres selected)
   - Growth Check shows ✅, ⚠️, ❌ sections
   - Copy button copies `.env` text to clipboard
   - "← Start Over" resets to the idea input stage with empty state

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/OutputPanel.jsx frontend/src/App.jsx
git commit -m "feat: output panel with PRD, .env copy, and growth check rendering"
```

---

## Self-Review

**Spec coverage:**
- ✅ Idea-first flow: idea → recommend → edit cards → generate
- ✅ `/recommend` endpoint: single LLM call returning summary + stack
- ✅ `/generate` endpoint: 4-stage pipeline (normalize, analyze, prd, growth) + deterministic env
- ✅ Card-based selection for scope/backend/frontend/APIs/database
- ✅ API key inputs appear on API card selection, fed into `.env`
- ✅ PRD rendered as markdown with all 6 sections
- ✅ `.env` deterministic, commented, required/optional marked
- ✅ Growth Check with ✅/⚠️/❌
- ✅ Loading states for both endpoints
- ✅ "Start Over" resets all state
- ✅ No auth, no database, no async orchestration, no over-engineering

**Placeholder scan:** No TBDs or incomplete steps found.

**Type consistency:** `selections` shape is consistent across `App.jsx`, `SelectionCards.jsx`, `RecommendationPanel.jsx`, and the `/generate` request body. `api_keys` dict flows correctly from UI through to `env_builder`.
