from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class GitHubError(Exception):
    status_code: int
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return f"GitHub API error ({self.status_code}): {self.message}"


class GitHubClient:
    def __init__(
        self,
        token: str,
        http: httpx.Client | None = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._http = http or httpx.Client(timeout=30.0)
        self._owns_http = http is None

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(self, method: str, path: str, json: Any | None = None) -> Any:
        url = f"{self._base_url}{path if path.startswith('/') else '/' + path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        resp = self._http.request(method, url, headers=headers, json=json)
        if 200 <= resp.status_code < 300:
            if resp.status_code == 204:
                return None
            return resp.json()

        message = "Request failed"
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                msg = payload.get("message")
                if msg:
                    message = str(msg)
                errors = payload.get("errors")
                if isinstance(errors, list) and errors:
                    first = errors[0]
                    if isinstance(first, dict):
                        parts = []
                        for k in ("resource", "field", "code", "message"):
                            v = first.get(k)
                            if v:
                                parts.append(str(v))
                        if parts:
                            message = f"{message} ({', '.join(parts)})"
        except Exception:
            pass

        raise GitHubError(status_code=resp.status_code, message=message)

    def create_repo_with_initial_commit(
        self,
        *,
        name: str,
        private: bool,
        files: dict[str, str],
        commit_message: str,
    ) -> dict[str, Any]:
        # Step 1: Create repository with auto_init=true to get initial branch + README
        repo = self._request(
            "POST",
            "/user/repos",
            json={"name": name, "private": private, "auto_init": True},
        )
        owner = (repo.get("owner") or {}).get("login")
        repo_name = repo.get("name") or name
        repo_url = repo.get("html_url")
        default_branch = repo.get("default_branch") or "main"
        if not owner or not repo_url:
            raise GitHubError(status_code=502, message="Unexpected GitHub response creating repository")

        # Step 2: Upload files using Contents API
        # This API naturally creates commits and is much simpler than low-level git operations
        created_files = []
        
        for path in sorted(files.keys()):
            content = files[path] or ""
            
            # For README.md, fetch existing SHA (auto_init creates default README)
            # For other files, we can create them without a SHA
            sha: str | None = None
            if path == "README.md":
                try:
                    existing = self._request(
                        "GET",
                        f"/repos/{owner}/{repo_name}/contents/{path}",
                    )
                    sha = existing.get("sha")
                except GitHubError as e:
                    # If README doesn't exist (unlikely with auto_init), proceed without SHA
                    if e.status_code != 404:
                        raise
            
            # Base64 encode content for GitHub Contents API
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            
            # Upload file using Contents API
            body: dict[str, Any] = {
                "message": commit_message,
                "content": encoded_content,
            }
            if sha:
                body["sha"] = sha
            
            self._request(
                "PUT",
                f"/repos/{owner}/{repo_name}/contents/{path}",
                json=body,
            )
            created_files.append(path)

        return {
            "repo_name": repo_name,
            "repo_url": repo_url,
            "default_branch": default_branch,
            "created_files": created_files,
        }
