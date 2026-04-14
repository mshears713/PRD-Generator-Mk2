import os
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from config import USE_FAKE_LLM, prd_decomposition_enabled
from services.github_bootstrap import (
    build_kickoff_prompt,
    build_scaffold_files,
    extract_title_from_markdown,
    next_name_with_suffix,
    slugify_repo_name,
    validate_repo_name_override,
)
from services.github_client import GitHubClient, GitHubError
from pipeline.recommender import get_recommendation
from pipeline.context_advisor import get_context_advice
from pipeline.option_advisor import get_all_option_advice
from pipeline.normalizer import normalize
from pipeline.analyzer import analyze
from pipeline.prd_gen import generate_prd
from pipeline.prd_decomposer import decompose_prds
from pipeline.growth import generate_growth_check
from pipeline.env_builder import build_env
from pipeline.question_generator import generate_dynamic_questions
from pipeline.answer_mapper import map_answers_to_constraints

load_dotenv()

app = FastAPI()
SESSIONS_FILE = Path(__file__).resolve().parent / "sessions.json"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev only — restrict to frontend origin before deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    idea: str
    constraints: dict = {}
    answers: Optional[dict] = None


class QuickSetupQuestionsRequest(BaseModel):
    idea: str


class IterateSessionRequest(BaseModel):
    feedback: str


class GenerateRequest(BaseModel):
    idea: str
    scope: str
    backend: str
    frontend: str
    apis: list[str] = []
    database: str
    api_keys: dict[str, str] = {}


class GenerateResponse(BaseModel):
    main_prd: str
    backend_prd: Optional[str] = None
    frontend_prd: Optional[str] = None
    env: str
    growth_check: dict
    # Backward-compat alias (legacy frontend expects `prd`)
    prd: str


class CreateRepoRequest(BaseModel):
    idea: Optional[str] = None
    main_prd: str
    backend_prd: Optional[str] = None
    frontend_prd: Optional[str] = None
    env: Optional[str] = None
    repo_name: Optional[str] = None
    private: bool = True


class CreateRepoResponse(BaseModel):
    repo_name: str
    repo_url: str
    kickoff_prompt: str
    created_files: list[str]


class RecommendedStack(BaseModel):
    scope: str
    backend: str
    frontend: str
    apis: list[str] = []
    database: str


class Rationale(BaseModel):
    scope: str
    backend: str
    frontend: str
    apis: str
    database: str


class ApiCandidate(BaseModel):
    id: str
    name: str
    category: str
    summary: Optional[str] = None
    status: str
    recommended: bool = False
    reason: str
    why_not: Optional[str] = None
    sponsored: Optional[bool] = None
    sponsor_note: Optional[str] = None
    best_for: list[str] = []
    avoid_when: list[str] = []
    tags: list[str] = []
    complexity: Optional[str] = None
    backend_required: Optional[bool] = None
    common_pairings: list[str] = []


class ApiCandidates(BaseModel):
    selected: list[ApiCandidate] = []
    candidates: list[ApiCandidate] = []
    rejected: list[ApiCandidate] = []


class ConstraintImpact(BaseModel):
    constraint: str
    impact: str


class Confidence(BaseModel):
    score: int
    reason: str


class OptionEvaluation(BaseModel):
    fit_score: int
    confidence: int
    complexity_cost: str
    reason: str
    benefits: list[str]
    drawbacks: list[str]
    why_not_recommended: Optional[str] = None
    learn_more_url: Optional[str] = None


class FieldOptions(BaseModel):
    recommended: str
    options: dict[str, OptionEvaluation]


class ArchitectureAdvice(BaseModel):
    scope: FieldOptions
    backend: FieldOptions
    frontend: FieldOptions
    database: FieldOptions


class DeploymentOption(BaseModel):
    name: str
    value: str
    recommended: bool
    reason_for_recommendation: str
    benefits: list[str]
    drawbacks: list[str]
    sponsored: Optional[bool] = None
    sponsor_info: Optional[dict] = None


class RecommendResponse(BaseModel):
    system_understanding: str
    system_type: str
    core_system_logic: str
    key_requirements: list[str]
    scope_boundaries: list[str]
    phased_plan: list[str]
    recommended: RecommendedStack
    rationale: Rationale
    api_candidates: Optional[ApiCandidates] = None
    constraint_impact: list[ConstraintImpact]
    assumptions: list[str]
    confidence: Confidence
    architecture: Optional[ArchitectureAdvice] = None
    deployment: Optional[list[DeploymentOption]] = None


def normalize_session_idea(session: dict) -> dict:
    """Safely convert stringified idea JSON to proper object."""
    if not session or "idea" not in session:
        return session
    idea = session["idea"]
    # If idea is a string that looks like JSON, parse it
    if isinstance(idea, str):
        try:
            # Try to parse as JSON
            parsed = json.loads(idea)
            session["idea"] = parsed
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, keep it as a plain string object
            session["idea"] = {"text": idea} if idea else {}
    return session


def load_sessions() -> list[dict]:
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        sessions = data if isinstance(data, list) else []
        # Normalize idea fields to ensure they're objects, not strings
        return [normalize_session_idea(s) for s in sessions]
    except json.JSONDecodeError:
        return []


def save_sessions(sessions: list[dict]) -> None:
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")


def get_latest_session() -> Optional[dict]:
    sessions = load_sessions()
    return sessions[-1] if sessions else None


def create_session(session_obj: dict) -> dict:
    sessions = load_sessions()
    sessions.append(session_obj)
    save_sessions(sessions)
    return session_obj


def find_session_index(sessions: list[dict], session_id: str) -> int:
    for i, session in enumerate(sessions):
        if session.get("id") == session_id:
            return i
    return -1


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if not USE_FAKE_LLM and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    try:
        if req.answers:
            fixed_answers = (req.answers or {}).get("fixed_answers") or {}
            dynamic_answers = (req.answers or {}).get("dynamic_answers") or {}
            mapped = map_answers_to_constraints(req.idea, fixed_answers, dynamic_answers)
            constraints = mapped.get("constraints") or {}
            derived = mapped.get("derived") or {}
        else:
            constraints = req.constraints or {}
            derived = {}

        result = get_recommendation(req.idea, constraints, derived=derived)
        advice = get_context_advice(req.idea, constraints, result.get("recommended", {}), derived=derived)
        option_advice = get_all_option_advice(req.idea, constraints, result.get("recommended", {}), derived=derived)
        result["architecture"] = option_advice
        result["deployment"] = advice.get("deployment")
        create_session({
            "id": str(uuid4()),
            "idea": req.idea,
            "constraints": constraints,
            "recommendation": result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return result
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")


@app.post("/quick-setup/questions")
def quick_setup_questions(req: QuickSetupQuestionsRequest):
    return {"questions": generate_dynamic_questions(req.idea)}


@app.get("/sessions/latest")
def latest_session():
    session = get_latest_session()
    if not session:
        return {"session": None}
    return {"session": session}


@app.get("/sessions")
def list_sessions():
    sessions = load_sessions()
    summaries = []
    for session in sessions:
        # Ensure idea is always an object
        idea = session.get("idea") or {}
        if isinstance(idea, str):
            try:
                idea = json.loads(idea)
            except (json.JSONDecodeError, ValueError):
                idea = {"text": idea}
        summaries.append(
            {
                "id": session.get("id"),
                "idea": idea,
                "created_at": session.get("created_at"),
                "updated_at": session.get("updated_at"),
            }
        )
    summaries.sort(key=lambda s: s.get("updated_at") or s.get("created_at") or "", reverse=True)
    return {"sessions": summaries}


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    sessions = load_sessions()
    idx = find_session_index(sessions, session_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[idx]
    # Ensure idea is always an object
    if session and "idea" in session:
        idea = session["idea"]
        if isinstance(idea, str):
            try:
                session["idea"] = json.loads(idea)
            except (json.JSONDecodeError, ValueError):
                session["idea"] = {"text": idea}
    return {"session": session}


@app.post("/sessions/{session_id}/iterate", response_model=RecommendResponse)
def iterate_session(session_id: str, req: IterateSessionRequest):
    if not USE_FAKE_LLM and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    sessions = load_sessions()
    idx = find_session_index(sessions, session_id)
    if idx < 0:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[idx]
    idea = session.get("idea") or ""
    constraints = session.get("constraints") or {}
    feedback = (req.feedback or "").strip()
    context_idea = idea if not feedback else f"{idea}\n\nUser feedback:\n{feedback}"

    try:
        result = get_recommendation(idea, constraints, derived={}, feedback=feedback)
        advice = get_context_advice(context_idea, constraints, result.get("recommended", {}), derived={})
        option_advice = get_all_option_advice(context_idea, constraints, result.get("recommended", {}), derived={})
        result["architecture"] = option_advice
        result["deployment"] = advice.get("deployment")
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")

    sessions[idx]["recommendation"] = result
    sessions[idx]["last_feedback"] = feedback
    sessions[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_sessions(sessions)
    return result


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    if not USE_FAKE_LLM and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    selections = {
        "scope": req.scope,
        "backend": req.backend,
        "frontend": req.frontend,
        "apis": req.apis,
        "database": req.database,
    }

    try:
        normalized = normalize(req.idea, selections)
        architecture = analyze(normalized)
        prd = generate_prd(normalized, architecture)
        extra_prds = None
        if prd_decomposition_enabled():
            extra_prds = decompose_prds(prd, normalized, architecture)
        growth_check = generate_growth_check(prd, selections, normalized)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")

    env = build_env(req.apis, req.api_keys, req.database)

    backend_prd = extra_prds.get("backend_prd") if extra_prds else None
    frontend_prd = extra_prds.get("frontend_prd") if extra_prds else None
    return {
        "main_prd": prd,
        "backend_prd": backend_prd,
        "frontend_prd": frontend_prd,
        "env": env,
        "growth_check": growth_check,
        "prd": prd,
    }


def _missing_github_token() -> None:
    raise HTTPException(
        status_code=400,
        detail="GITHUB_TOKEN not set. Set it to use Create GitHub Repo.",
    )


def _looks_like_name_conflict(err: GitHubError) -> bool:
    if err.status_code != 422:
        return False
    msg = (err.message or "").lower()
    return "name already exists" in msg or "already exists" in msg


@app.post("/create-repo", response_model=CreateRepoResponse)
def create_repo(req: CreateRepoRequest):
    token = (os.getenv("GITHUB_TOKEN") or "").strip()
    if not token:
        _missing_github_token()

    try:
        if req.repo_name:
            validate_repo_name_override(req.repo_name)
            base_name = req.repo_name.strip()
        else:
            title = extract_title_from_markdown(req.main_prd) or (req.idea or "")
            base_name = slugify_repo_name(title)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    files = build_scaffold_files(
        main_prd=req.main_prd,
        backend_prd=req.backend_prd,
        frontend_prd=req.frontend_prd,
        env_text=req.env,
    )

    commit_message = "Initial project scaffold from StackLens"

    last_err: GitHubError | None = None
    client = GitHubClient(token=token)
    try:
        for attempt in range(0, 6):
            name = base_name if attempt == 0 else next_name_with_suffix(base_name, attempt)
            try:
                created = client.create_repo_with_initial_commit(
                    name=name,
                    private=req.private,
                    files=files,
                    commit_message=commit_message,
                )
                repo_url = created["repo_url"]
                kickoff = build_kickoff_prompt(repo_url=repo_url, has_frontend=bool(req.frontend_prd))
                return {
                    "repo_name": created["repo_name"],
                    "repo_url": repo_url,
                    "kickoff_prompt": kickoff,
                    "created_files": created.get("created_files") or sorted(files.keys()),
                }
            except GitHubError as e:
                last_err = e
                if attempt < 5 and _looks_like_name_conflict(e) and not req.repo_name:
                    continue
                raise HTTPException(status_code=e.status_code, detail=str(e))
    finally:
        client.close()

    if last_err:
        raise HTTPException(status_code=last_err.status_code, detail=str(last_err))
    raise HTTPException(status_code=500, detail="Unknown error creating repository")
