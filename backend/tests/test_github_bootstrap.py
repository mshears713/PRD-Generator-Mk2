import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from fastapi.testclient import TestClient

from main import app
from services.github_bootstrap import (
    build_kickoff_prompt,
    next_name_with_suffix,
    sanitize_env_example,
    slugify_repo_name,
)
from services.github_client import GitHubClient, GitHubError


client = TestClient(app)


def test_slugify_repo_name_basic():
    assert slugify_repo_name("AI Journaling Assistant") == "ai-journaling-assistant"
    assert slugify_repo_name("  ") == "stacklens-project"
    assert slugify_repo_name("Hello, World!!!") == "hello-world"


def test_slugify_repo_name_truncates_to_100():
    long = "a" * 200
    assert len(slugify_repo_name(long)) == 100


def test_sanitize_env_example_strips_values_and_keeps_comments():
    env_text = "# comment\nFOO=bar\nEMPTY=\nSPACED = value\nNOEQUALS\n"
    out = sanitize_env_example(env_text)
    assert "# comment" in out
    assert "FOO=" in out
    assert "EMPTY=" in out
    assert "SPACED=" in out
    assert "NOEQUALS" in out
    assert "bar" not in out
    assert "value" not in out


def test_kickoff_prompt_includes_frontend_conditionally():
    p1 = build_kickoff_prompt("https://github.com/x/y", has_frontend=False)
    assert "frontend_prd.md" not in p1
    p2 = build_kickoff_prompt("https://github.com/x/y", has_frontend=True)
    assert "frontend_prd.md" in p2


def test_next_name_with_suffix_trims_if_needed():
    base = "a" * 100
    n = next_name_with_suffix(base, 1)
    assert n.endswith("-1")
    assert len(n) <= 100


def test_create_repo_missing_token_returns_400(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    payload = {
        "idea": "x",
        "main_prd": "# Title\n\nBody",
        "backend_prd": "b",
        "frontend_prd": None,
        "env": "FOO=bar\n",
        "repo_name": None,
        "private": True,
    }
    res = client.post("/create-repo", json=payload)
    assert res.status_code == 400
    assert "GITHUB_TOKEN not set" in res.json()["detail"]


def test_create_repo_success_contract(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")

    def fake_create(self, *, name, private, files, commit_message):
        assert private is True
        assert "README.md" in files
        return {
            "repo_name": name,
            "repo_url": f"https://github.com/me/{name}",
            "default_branch": "main",
            "created_files": sorted(files.keys()),
        }

    monkeypatch.setattr(GitHubClient, "create_repo_with_initial_commit", fake_create)

    payload = {
        "idea": "AI Journaling Assistant",
        "main_prd": "# AI Journaling Assistant\n\nBody",
        "backend_prd": "backend",
        "frontend_prd": "frontend",
        "env": "OPENAI_API_KEY=sk-test\n",
        "repo_name": None,
        "private": True,
    }
    res = client.post("/create-repo", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["repo_name"]
    assert data["repo_url"].startswith("https://github.com/")
    assert "kickoff_prompt" in data
    assert isinstance(data["created_files"], list)
    assert "frontend_prd.md" in data["created_files"]


def test_create_repo_retries_on_name_conflict(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    calls = {"n": 0, "names": []}

    def fake_create(self, *, name, private, files, commit_message):
        calls["n"] += 1
        calls["names"].append(name)
        if calls["n"] == 1:
            raise GitHubError(status_code=422, message="Repository creation failed. (name already exists)")
        return {
            "repo_name": name,
            "repo_url": f"https://github.com/me/{name}",
            "default_branch": "main",
            "created_files": sorted(files.keys()),
        }

    monkeypatch.setattr(GitHubClient, "create_repo_with_initial_commit", fake_create)

    payload = {
        "idea": "My Project",
        "main_prd": "# My Project\n\nBody",
        "backend_prd": "backend",
        "frontend_prd": None,
        "env": "FOO=bar\n",
        "repo_name": None,
        "private": True,
    }
    res = client.post("/create-repo", json=payload)
    assert res.status_code == 200
    assert calls["n"] == 2
    assert calls["names"][0] == "my-project"
    assert calls["names"][1].startswith("my-project-")


def test_github_client_simplified_contents_api_flow():
    """Test that repo creation uses auto_init=true and Contents API."""
    class DummyResp:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class DummyHTTP:
        def __init__(self):
            self.calls = []
            self._request_count = 0

        def request(self, method, url, headers=None, json=None):
            self.calls.append((method, url, json))
            self._request_count += 1

            # Step 1: Initial repo creation with auto_init=true
            if method == "POST" and url.endswith("/user/repos"):
                # Verify auto_init=true was passed
                assert json.get("auto_init") is True, "Should create repo with auto_init=true"
                return DummyResp(
                    201,
                    {
                        "name": "demo",
                        "html_url": "https://github.com/me/demo",
                        "default_branch": "main",
                        "owner": {"login": "me"},
                    },
                )

            # Step 2: GET request to check existing README (auto-created)
            if method == "GET" and "/contents/README.md" in url:
                return DummyResp(200, {"sha": "existing-readme-sha", "name": "README.md"})

            # Step 3: PUT requests for file uploads using Contents API
            if method == "PUT" and "/contents/" in url:
                # Verify message and content are present
                assert json.get("message") == "Initial project scaffold from StackLens"
                assert "content" in json
                return DummyResp(201, {"commit": {"sha": f"commit{self._request_count}"}})

            return DummyResp(500, {"message": "unexpected request"})

    http = DummyHTTP()
    gh = GitHubClient(token="t", http=http, base_url="https://api.github.com")
    out = gh.create_repo_with_initial_commit(
        name="demo",
        private=True,
        files={"README.md": "new readme", "backend_prd.md": "backend content"},
        commit_message="Initial project scaffold from StackLens",
    )

    assert out["repo_url"] == "https://github.com/me/demo"
    assert out["repo_name"] == "demo"
    assert out["created_files"] == ["README.md", "backend_prd.md"]

    # Verify API call sequence
    assert len([c for c in http.calls if c[0] == "POST" and c[1].endswith("/user/repos")]) == 1
    assert len([c for c in http.calls if c[0] == "GET" and "README.md" in c[1]]) == 1
    assert len([c for c in http.calls if c[0] == "PUT" and "/contents/" in c[1]]) == 2

    # Verify no low-level git operations (blobs, trees, commits, refs)
    assert not any("/git/blobs" in c[1] for c in http.calls)
    assert not any("/git/trees" in c[1] for c in http.calls)
    assert not any("/git/commits" in c[1] for c in http.calls)
    assert not any("/git/refs" in c[1] for c in http.calls)


def test_github_client_handles_multiple_files_with_frontend_prd():
    """Test file upload with all scaffold files including frontend_prd."""
    class DummyResp:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class DummyHTTP:
        def __init__(self):
            self.calls = []

        def request(self, method, url, headers=None, json=None):
            self.calls.append((method, url, json))

            if method == "POST" and url.endswith("/user/repos"):
                return DummyResp(
                    201,
                    {
                        "name": "fullstack-app",
                        "html_url": "https://github.com/me/fullstack-app",
                        "default_branch": "main",
                        "owner": {"login": "me"},
                    },
                )

            if method == "GET" and "/contents/README.md" in url:
                return DummyResp(200, {"sha": "sha123"})

            if method == "PUT" and "/contents/" in url:
                return DummyResp(201, {"commit": {"sha": "newcommitsha"}})

            return DummyResp(500, {"message": "unexpected"})

    http = DummyHTTP()
    gh = GitHubClient(token="t", http=http, base_url="https://api.github.com")
    out = gh.create_repo_with_initial_commit(
        name="fullstack-app",
        private=False,
        files={
            "README.md": "# App",
            "backend_prd.md": "backend",
            "frontend_prd.md": "frontend",
            ".env.example": "API_KEY=",
            ".gitignore": "*.pyc",
            "backend/main.py": "from fastapi import FastAPI",
            "backend/requirements.txt": "fastapi>=0.80.0",
        },
        commit_message="Initial project scaffold from StackLens",
    )

    # Should upload all 7 files
    assert len(out["created_files"]) == 7
    assert "frontend_prd.md" in out["created_files"]
    put_calls = [c for c in http.calls if c[0] == "PUT"]
    assert len(put_calls) == 7


def test_github_client_readme_sha_missing_on_404():
    """Test that README creation works even if GET returns 404 (shouldn't happen with auto_init)."""
    class DummyResp:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class DummyHTTP:
        def __init__(self):
            self.calls = []

        def request(self, method, url, headers=None, json=None):
            self.calls.append((method, url, json))

            if method == "POST" and url.endswith("/user/repos"):
                return DummyResp(
                    201,
                    {
                        "name": "test",
                        "html_url": "https://github.com/me/test",
                        "default_branch": "main",
                        "owner": {"login": "me"},
                    },
                )

            if method == "GET" and "/contents/README.md" in url:
                # Simulate 404 - README doesn't exist (edge case)
                raise GitHubError(status_code=404, message="Not Found")

            if method == "PUT" and "/contents/" in url:
                return DummyResp(201, {"commit": {"sha": "commitsha"}})

            return DummyResp(500, {"message": "unexpected"})

    http = DummyHTTP()
    gh = GitHubClient(token="t", http=http, base_url="https://api.github.com")
    out = gh.create_repo_with_initial_commit(
        name="test",
        private=True,
        files={"README.md": "content"},
        commit_message="msg",
    )

    assert out["created_files"] == ["README.md"]
    # Should still create the file (PUT without sha for 404 case)
    put_calls = [c for c in http.calls if c[0] == "PUT"]
    assert len(put_calls) == 1

