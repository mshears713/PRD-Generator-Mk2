import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from config import USE_FAKE_LLM
from pipeline.recommender import get_recommendation
from pipeline.context_advisor import get_context_advice
from pipeline.option_advisor import get_all_option_advice
from pipeline.normalizer import normalize
from pipeline.analyzer import analyze
from pipeline.prd_gen import generate_prd
from pipeline.growth import generate_growth_check
from pipeline.env_builder import build_env
from pipeline.question_generator import generate_dynamic_questions
from pipeline.answer_mapper import map_answers_to_constraints

load_dotenv()

app = FastAPI()

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


class GenerateRequest(BaseModel):
    idea: str
    scope: str
    backend: str
    frontend: str
    apis: list[str] = []
    database: str
    api_keys: dict[str, str] = {}


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
        return result
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")


@app.post("/quick-setup/questions")
def quick_setup_questions(req: QuickSetupQuestionsRequest):
    return {"questions": generate_dynamic_questions(req.idea)}


@app.post("/generate")
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
        growth_check = generate_growth_check(prd, selections, normalized)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")

    env = build_env(req.apis, req.api_keys, req.database)

    return {"prd": prd, "env": env, "growth_check": growth_check}
