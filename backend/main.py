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
        result = get_recommendation(req.idea, req.constraints)
        advice = get_context_advice(req.idea, req.constraints, result.get("recommended", {}))
        option_advice = get_all_option_advice(req.idea, req.constraints, result.get("recommended", {}))
        result["architecture"] = option_advice
        result["deployment"] = advice.get("deployment")
        return result
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")


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
