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
    allow_origins=["*"],  # Dev only — restrict to frontend origin before deployment
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
    try:
        return get_recommendation(req.idea)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")


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

    try:
        normalized = normalize(req.idea, selections)
        architecture = analyze(normalized)
        prd = generate_prd(normalized, architecture)
        growth_check = generate_growth_check(prd, selections)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM response error: {e}")

    env = build_env(req.apis, req.api_keys, req.database)

    return {"prd": prd, "env": env, "growth_check": growth_check}
