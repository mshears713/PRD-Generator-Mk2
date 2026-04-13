from __future__ import annotations

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
        created_files = sorted(files.keys())

        repo = self._request(
            "POST",
            "/user/repos",
            json={"name": name, "private": private, "auto_init": False},
        )
        owner = (repo.get("owner") or {}).get("login")
        repo_name = repo.get("name") or name
        repo_url = repo.get("html_url")
        default_branch = repo.get("default_branch") or "main"
        if not owner or not repo_url:
            raise GitHubError(status_code=502, message="Unexpected GitHub response creating repository")

        blobs: dict[str, str] = {}
        for path, content in files.items():
            blob = self._request(
                "POST",
                f"/repos/{owner}/{repo_name}/git/blobs",
                json={"content": content, "encoding": "utf-8"},
            )
            sha = blob.get("sha")
            if not sha:
                raise GitHubError(status_code=502, message=f"Unexpected GitHub response creating blob for {path}")
            blobs[path] = sha

        tree_items = []
        for path, sha in blobs.items():
            tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": sha})

        tree = self._request(
            "POST",
            f"/repos/{owner}/{repo_name}/git/trees",
            json={"tree": tree_items},
        )
        tree_sha = tree.get("sha")
        if not tree_sha:
            raise GitHubError(status_code=502, message="Unexpected GitHub response creating tree")

        commit = self._request(
            "POST",
            f"/repos/{owner}/{repo_name}/git/commits",
            json={"message": commit_message, "tree": tree_sha, "parents": []},
        )
        commit_sha = commit.get("sha")
        if not commit_sha:
            raise GitHubError(status_code=502, message="Unexpected GitHub response creating commit")

        self._request(
            "POST",
            f"/repos/{owner}/{repo_name}/git/refs",
            json={"ref": f"refs/heads/{default_branch}", "sha": commit_sha},
        )

        return {
            "repo_name": repo_name,
            "repo_url": repo_url,
            "default_branch": default_branch,
            "created_files": created_files,
        }
