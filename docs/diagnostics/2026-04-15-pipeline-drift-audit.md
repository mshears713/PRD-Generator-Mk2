# Diagnostic Audit: Architecture Drift in LLM Pipeline (Observation Only)

## 1) Executive Summary

- **First corruption point:** `recommender` pre-LLM decision scaffold introduces architecture assumptions before PRD generation.
- **Primary driver:** pipeline-level defaults/injection (not only LLM free-form reasoning).
- **Key symptom path:** unconstrained idea -> scaffold infers backend/API needs -> recommendation hardens stack -> normalizer/analyzer overwrite details to match stack -> PRD inherits those decisions.
- **Result:** PRD is mostly reflecting earlier injected assumptions, with additional template language from PRD prompt + fake-LLM fallback behavior in this environment.

## 2) Full Pipeline Trace (raw data per stage)

### Trace input

```json
{
  "idea": "A tool that summarizes my daily notes and gives me one action plan.",
  "constraints": {}
}
```

### Recommender output

```json
{
  "system_understanding": "The system serves users working on 'A tool that summarizes my daily notes and gives me one action plan.' with constraints=default. Inputs enter through a simple UI or API, are processed by the core service, and return immediate results. Computation runs on the backend when needed, with storage determined by persistence needs. The flow stays focused on the primary use case and avoids extra infrastructure not required by the constraints.",
  "system_type": "AI assistant",
  "core_system_logic": "Core logic ingests the primary user input, applies the main transformation or workflow, and returns a structured response with any stored state updated if persistence is required.",
  "key_requirements": [
    "Deterministic handling of the primary user workflow",
    "Clear API boundaries between input, processing, and output",
    "Constraint-aligned data storage and retrieval"
  ],
  "scope_boundaries": [
    "In scope: the primary workflow for the stated idea",
    "Out of scope: advanced analytics or multi-tenant scaling beyond the stated constraints",
    "Out of scope: complex integrations unless explicitly required"
  ],
  "phased_plan": [
    "Phase 1: Core \u2014 build the primary workflow and minimal data model",
    "Phase 2: Harden \u2014 add validation, monitoring, and edge case handling",
    "Phase 3: Extend \u2014 optional integrations or workflow enhancements"
  ],
  "recommended": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": [
      "openrouter",
      "upstash_redis"
    ],
    "database": "none"
  },
  "rationale": {
    "scope": "Chosen scope aligns with constraints=default and keeps the build aligned to the required system shape.",
    "backend": "Backend selection fits constraints=default and supports the required execution path without excess overhead.",
    "frontend": "Frontend choice reflects constraints=default and the needed user interaction surface for this idea.",
    "apis": "APIs chosen for project signals. Selected: OpenRouter, Upstash Redis. Not chosen: Tavily, SerpAPI, Brave Search API.",
    "database": "Database choice matches constraints=default and the persistence needs implied by the idea."
  },
  "constraint_impact": [],
  "assumptions": [
    "Assuming single-user usage with no concurrent load requirements",
    "Assuming no authentication unless later required",
    "Assuming text-only input/output unless other data types are specified",
    "Assuming no long-term storage unless explicitly required",
    "Assuming synchronous processing unless async is specified",
    "Assuming a simple single-step tool unless a workflow is specified"
  ],
  "confidence": {
    "score": 50,
    "reason": "Confidence reflects how many constraint details were assumed versus explicitly provided."
  },
  "api_candidates": {
    "selected": [
      {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "ai_inference",
        "status": "selected",
        "recommended": true,
        "reason": "LLM is core; OpenRouter keeps model choice flexible.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "LLM gateway providing access to many providers with one API key.",
        "best_for": [
          "AI-first products needing fast model iteration",
          "Teams wanting fallback routing across LLMs"
        ],
        "avoid_when": [
          "Strict single-vendor SLA requirements",
          "Offline or on-prem constraints"
        ],
        "tags": [
          "llm",
          "routing",
          "multi-provider"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "postgres",
          "supabase",
          "tavily"
        ]
      },
      {
        "id": "upstash_redis",
        "name": "Upstash Redis",
        "category": "database",
        "status": "selected",
        "recommended": true,
        "reason": "Data/storage needs require this database tier.",
        "why_not": null,
        "sponsored": true,
        "sponsor_note": "Sponsored option: sign up bonus / builder credit messaging",
        "summary": "Serverless Redis API for low-latency caches and queues.",
        "best_for": [
          "Ephemeral cache or queues",
          "Realtime or rate-limited workloads"
        ],
        "avoid_when": [
          "Needs relational durability",
          "Large relational schemas"
        ],
        "tags": [
          "redis",
          "cache",
          "queue"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "fastapi",
          "node",
          "openrouter"
        ]
      }
    ],
    "candidates": [
      {
        "id": "openai",
        "name": "OpenAI API",
        "category": "ai_inference",
        "status": "candidate",
        "recommended": false,
        "reason": "LLM required; useful alternative provider for coverage.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Direct access to OpenAI GPT and embeddings models.",
        "best_for": [
          "Projects requiring GPT-4o or o3 reasoning",
          "Teams standardizing on OpenAI pricing"
        ],
        "avoid_when": [
          "Need provider redundancy",
          "Hard compliance limits on US-hosted data"
        ],
        "tags": [
          "llm",
          "completion",
          "embedding"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "postgres",
          "tavily"
        ]
      },
      {
        "id": "anthropic",
        "name": "Anthropic",
        "category": "ai_inference",
        "status": "candidate",
        "recommended": false,
        "reason": "LLM required; useful alternative provider for coverage.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Claude family models for safer, longer-context reasoning.",
        "best_for": [
          "Safety-sensitive assistants",
          "Long-context analysis"
        ],
        "avoid_when": [
          "GPU/image heavy multimodal",
          "Need provider diversity"
        ],
        "tags": [
          "llm",
          "reasoning",
          "safety"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "postgres",
          "openrouter"
        ]
      },
      {
        "id": "postgres",
        "name": "Postgres",
        "category": "database",
        "status": "candidate",
        "recommended": false,
        "reason": "Viable database depending on final data shape.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Relational SQL database for durable data.",
        "best_for": [
          "Structured data with relationships",
          "Long-term durability"
        ],
        "avoid_when": [
          "Purely ephemeral data",
          "No backend available"
        ],
        "tags": [
          "sql",
          "relational",
          "durable"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "fastapi",
          "node",
          "openrouter"
        ]
      },
      {
        "id": "supabase",
        "name": "Supabase",
        "category": "database",
        "status": "candidate",
        "recommended": false,
        "reason": "Viable database depending on final data shape.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Hosted Postgres with auth, storage, and realtime APIs.",
        "best_for": [
          "Small teams needing instant auth + DB",
          "Realtime channel updates"
        ],
        "avoid_when": [
          "Heavy custom Postgres extensions",
          "On-prem requirements"
        ],
        "tags": [
          "sql",
          "auth",
          "realtime"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "react",
          "node",
          "openrouter"
        ]
      }
    ],
    "rejected": [
      {
        "id": "tavily",
        "name": "Tavily",
        "category": "research_search",
        "status": "rejected",
        "recommended": false,
        "reason": "No external web search requirement detected.",
        "why_not": "needs_search=false",
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Structured web search API tuned for LLM agents.",
        "best_for": [
          "Live web enrichment for answers",
          "Agent-style retrieval"
        ],
        "avoid_when": [
          "No external data needed",
          "Offline environments"
        ],
        "tags": [
          "search",
          "web",
          "research"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "openrouter",
          "openai"
        ]
      },
      {
        "id": "serpapi",
        "name": "SerpAPI",
        "category": "research_search",
        "status": "rejected",
        "recommended": false,
        "reason": "No external web search requirement detected.",
        "why_not": "needs_search=false",
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Google search results API with rich SERP data.",
        "best_for": [
          "Google SERP-style scraping",
          "SEO and ranking data"
        ],
        "avoid_when": [
          "Need structured citations",
          "Cost sensitivity"
        ],
        "tags": [
          "search",
          "google",
          "serp"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "postgres",
          "openai"
        ]
      },
      {
        "id": "brave_search",
        "name": "Brave Search API",
        "category": "research_search",
        "status": "rejected",
        "recommended": false,
        "reason": "No external web search requirement detected.",
        "why_not": "needs_search=false",
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Privacy-focused web search results via Brave index.",
        "best_for": [
          "Privacy-conscious search",
          "Alternate index redundancy"
        ],
        "avoid_when": [
          "Need Google-specific results"
        ],
        "tags": [
          "search",
          "privacy"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "openrouter",
          "openai"
        ]
      },
      {
        "id": "mapbox",
        "name": "Mapbox",
        "category": "maps",
        "status": "rejected",
        "recommended": false,
        "reason": "Mapping not indicated.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Maps, geocoding, and tiles with strong styling control.",
        "best_for": [
          "Custom styled maps",
          "Mobile-friendly tiles"
        ],
        "avoid_when": [
          "Need Google Places data",
          "Ultra-low cost"
        ],
        "tags": [
          "maps",
          "geocoding",
          "tiles"
        ],
        "complexity": "medium",
        "backend_required": false,
        "common_pairings": [
          "react",
          "node"
        ]
      },
      {
        "id": "google_maps_platform",
        "name": "Google Maps Platform",
        "category": "maps",
        "status": "rejected",
        "recommended": false,
        "reason": "Mapping not indicated.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Google Maps, Places, and routes APIs.",
        "best_for": [
          "Place search and autocomplete",
          "Routing with traffic"
        ],
        "avoid_when": [
          "Strict privacy requirements",
          "Need custom tile styling"
        ],
        "tags": [
          "maps",
          "places",
          "routing"
        ],
        "complexity": "medium",
        "backend_required": false,
        "common_pairings": [
          "react",
          "firebase"
        ]
      },
      {
        "id": "blaxel",
        "name": "Blaxel",
        "category": "testing",
        "status": "rejected",
        "recommended": false,
        "reason": "Testing support not requested.",
        "why_not": "testing=false",
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Hosted testing and validation platform for app workflows.",
        "best_for": [
          "Teams wanting guided validation",
          "CI-friendly hosted checks"
        ],
        "avoid_when": [
          "No testing budget",
          "Local-only projects"
        ],
        "tags": [
          "testing",
          "validation",
          "ci"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "fastapi",
          "react",
          "postgres"
        ]
      },
      {
        "id": "playwright",
        "name": "Playwright",
        "category": "automation_browser",
        "status": "rejected",
        "recommended": false,
        "reason": "No browser automation requirement detected.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Headless browser automation for testing and scraping.",
        "best_for": [
          "Deterministic browser automation",
          "E2E tests with multi-browser support"
        ],
        "avoid_when": [
          "Need hosted browser infra",
          "Non-browser automation"
        ],
        "tags": [
          "automation",
          "browser",
          "testing"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "node",
          "blaxel"
        ]
      },
      {
        "id": "browserbase",
        "name": "Browserbase",
        "category": "automation_browser",
        "status": "rejected",
        "recommended": false,
        "reason": "No browser automation requirement detected.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Hosted headless Chrome sessions with programmatic control.",
        "best_for": [
          "Scale browser automation without self-hosting",
          "Avoid CAPTCHAs with managed sessions"
        ],
        "avoid_when": [
          "Local/offline automation"
        ],
        "tags": [
          "automation",
          "hosted",
          "browser"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "playwright",
          "node"
        ]
      },
      {
        "id": "notion_api",
        "name": "Notion API",
        "category": "docs_collaboration",
        "status": "rejected",
        "recommended": false,
        "reason": "Docs/collaboration not required.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Read/write access to Notion pages and databases.",
        "best_for": [
          "Docs sync with Notion",
          "Lightweight CMS"
        ],
        "avoid_when": [
          "No Notion usage",
          "Strict on-prem requirements"
        ],
        "tags": [
          "docs",
          "collaboration",
          "workspace"
        ],
        "complexity": "low",
        "backend_required": true,
        "common_pairings": [
          "slack_api",
          "openrouter"
        ]
      },
      {
        "id": "slack_api",
        "name": "Slack API",
        "category": "docs_collaboration",
        "status": "rejected",
        "recommended": false,
        "reason": "Docs/collaboration not required.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Messaging, slash commands, and webhooks for Slack workspaces.",
        "best_for": [
          "Notifications and workflows inside Slack",
          "Chat-based interactions"
        ],
        "avoid_when": [
          "No Slack usage",
          "Highly regulated data"
        ],
        "tags": [
          "chat",
          "notifications",
          "webhooks"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "notion_api",
          "openrouter"
        ]
      },
      {
        "id": "google_docs_drive",
        "name": "Google Docs / Drive API",
        "category": "docs_collaboration",
        "status": "rejected",
        "recommended": false,
        "reason": "Docs/collaboration not required.",
        "why_not": null,
        "sponsored": false,
        "sponsor_note": null,
        "summary": "Programmatic access to Google Docs and Drive files.",
        "best_for": [
          "Doc generation and sharing",
          "Drive file automation"
        ],
        "avoid_when": [
          "Strict data residency outside Google",
          "No Google Workspace"
        ],
        "tags": [
          "docs",
          "drive",
          "automation"
        ],
        "complexity": "medium",
        "backend_required": true,
        "common_pairings": [
          "openrouter",
          "notion_api"
        ]
      }
    ]
  }
}
```

### Context advisor output

```json
{
  "architecture": {
    "scope": {
      "choice": "backend",
      "reason_for_recommendation": "Chosen because constraints=default and it matches the core system needs.",
      "benefits": [
        "Supports constraints=default without adding unnecessary overhead",
        "Keeps delivery focused on the primary workflow"
      ],
      "drawbacks": [
        "May require adjustments if constraints change significantly."
      ],
      "learn_more_url": null
    },
    "backend": {
      "choice": "fastapi",
      "reason_for_recommendation": "Chosen because constraints=default and it matches the core system needs.",
      "benefits": [
        "Supports constraints=default without adding unnecessary overhead",
        "Keeps delivery focused on the primary workflow"
      ],
      "drawbacks": [
        "May require adjustments if constraints change significantly."
      ],
      "learn_more_url": "https://fastapi.tiangolo.com/"
    },
    "frontend": {
      "choice": "none",
      "reason_for_recommendation": "Chosen because constraints=default and it matches the core system needs.",
      "benefits": [
        "Supports constraints=default without adding unnecessary overhead",
        "Keeps delivery focused on the primary workflow"
      ],
      "drawbacks": [
        "May require adjustments if constraints change significantly."
      ],
      "learn_more_url": null
    },
    "database": {
      "choice": "none",
      "reason_for_recommendation": "Chosen because constraints=default and it matches the core system needs.",
      "benefits": [
        "Supports constraints=default without adding unnecessary overhead",
        "Keeps delivery focused on the primary workflow"
      ],
      "drawbacks": [
        "May require adjustments if constraints change significantly."
      ],
      "learn_more_url": null
    }
  },
  "deployment": [
    {
      "name": "Render",
      "value": "render",
      "recommended": true,
      "reason_for_recommendation": "Best fit for fast delivery with minimal infrastructure overhead.",
      "benefits": [
        "Quick setup for a small team",
        "Easy scaling for early usage"
      ],
      "drawbacks": [
        "Limited deep infrastructure control compared to AWS"
      ],
      "sponsored": true,
      "sponsor_info": {
        "why_use": [
          "Simple deployment for the current scope",
          "Costs align with early-stage usage"
        ],
        "bonus": "Free tier + simple scaling"
      },
      "learn_more_url": "https://render.com/docs"
    },
    {
      "name": "AWS",
      "value": "aws",
      "recommended": false,
      "reason_for_recommendation": "Overkill for the current constraints and scope.",
      "benefits": [
        "High flexibility for large-scale needs"
      ],
      "drawbacks": [
        "More configuration and operational overhead"
      ],
      "sponsored": false,
      "learn_more_url": "https://docs.aws.amazon.com/"
    },
    {
      "name": "Self-hosted",
      "value": "self",
      "recommended": false,
      "reason_for_recommendation": "Adds maintenance burden without clear benefit at this scale.",
      "benefits": [
        "Full control over environment"
      ],
      "drawbacks": [
        "Requires ongoing ops work"
      ],
      "sponsored": false,
      "learn_more_url": null
    }
  ]
}
```

### Option advisor output

```json
{
  "scope": {
    "recommended": "backend",
    "options": {
      "frontend": {
        "fit_score": 72,
        "confidence": 68,
        "complexity_cost": "low",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": null
      },
      "backend": {
        "fit_score": 88,
        "confidence": 75,
        "complexity_cost": "medium",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": null
      },
      "fullstack": {
        "fit_score": 65,
        "confidence": 66,
        "complexity_cost": "high",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": "Score below 70 because it conflicts with the stated constraints or required execution model.",
        "learn_more_url": null
      }
    }
  },
  "backend": {
    "recommended": "fastapi",
    "options": {
      "fastapi": {
        "fit_score": 92,
        "confidence": 76,
        "complexity_cost": "medium",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": "https://fastapi.tiangolo.com/"
      },
      "node": {
        "fit_score": 80,
        "confidence": 72,
        "complexity_cost": "medium",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": "https://nodejs.org/en/docs"
      },
      "none": {
        "fit_score": 30,
        "confidence": 52,
        "complexity_cost": "low",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": "Score below 70 because it conflicts with the stated constraints or required execution model.",
        "learn_more_url": null
      }
    }
  },
  "frontend": {
    "recommended": "none",
    "options": {
      "react": {
        "fit_score": 60,
        "confidence": 64,
        "complexity_cost": "medium",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": "Score below 70 because it conflicts with the stated constraints or required execution model.",
        "learn_more_url": "https://react.dev/"
      },
      "static": {
        "fit_score": 65,
        "confidence": 66,
        "complexity_cost": "low",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": "Score below 70 because it conflicts with the stated constraints or required execution model.",
        "learn_more_url": null
      },
      "none": {
        "fit_score": 82,
        "confidence": 72,
        "complexity_cost": "low",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": null
      }
    }
  },
  "database": {
    "recommended": "none",
    "options": {
      "postgres": {
        "fit_score": 88,
        "confidence": 75,
        "complexity_cost": "high",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": "https://www.postgresql.org/docs/"
      },
      "firebase": {
        "fit_score": 70,
        "confidence": 68,
        "complexity_cost": "medium",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": null,
        "learn_more_url": "https://firebase.google.com/docs"
      },
      "none": {
        "fit_score": 25,
        "confidence": 50,
        "complexity_cost": "low",
        "reason": "This option fits the project because constraints=default and the system behavior implied by 'A tool that summarizes my daily notes and gives me one action plan.'.",
        "benefits": [
          "Aligns with constraints=default while keeping the workflow focused",
          "Keeps implementation overhead proportional to the stated requirements"
        ],
        "drawbacks": [
          "May require extra effort if the project scope expands beyond current constraints."
        ],
        "why_not_recommended": "Score below 70 because it conflicts with the stated constraints or required execution model.",
        "learn_more_url": null
      }
    }
  }
}
```

### Normalizer output

```json
{
  "system_name": "AToolThat",
  "purpose": "Provide a concrete implementation of 'A tool that summarizes my daily notes and gives me one action plan.' for the target users.",
  "core_features": [
    "Primary user workflow",
    "Structured input validation",
    "Deterministic output formatting",
    "Basic error handling"
  ],
  "user_types": [
    "Primary user"
  ],
  "input_output": [
    "Step 1: Client sends HTTP request directly to the API",
    "Step 2: FastAPI endpoint validates request and routes to core logic",
    "Step 3: Core logic processes the request deterministically",
    "Step 4: JSON response returned (no persistence)"
  ],
  "data_model": [
    "No persistent data stored"
  ],
  "constraints": [
    "Backend selected: fastapi",
    "Frontend selected: none",
    "Database selected: none",
    "APIs selected: openrouter, upstash_redis"
  ],
  "assumptions": [
    "Assuming text-based user input only",
    "Assuming single-user concurrency",
    "Assuming no authentication unless added later"
  ],
  "unknowns": [
    "Scaling expectations not provided",
    "Latency budget unspecified"
  ],
  "selected_stack": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": [
      "openrouter",
      "upstash_redis"
    ],
    "database": "none"
  }
}
```

### Analyzer output

```json
{
  "components": [
    {
      "name": "FastAPI API Layer",
      "responsibility": "Handles incoming requests and returns responses"
    },
    {
      "name": "Core Service",
      "responsibility": "Executes the main business logic"
    }
  ],
  "data_flow": [
    "Step 1: Client calls API endpoint",
    "Step 2: Core service processes the input",
    "Step 3: Results are returned to the client"
  ],
  "dependencies": [
    "API Layer calls Core Service for processing"
  ],
  "risks": [
    "Ambiguous requirements could lead to rework",
    "Scaling assumptions may need revision"
  ],
  "failure_points": [
    "API layer returns 500 if downstream LLM/logic errors"
  ],
  "minimal_mvp_components": [
    "FastAPI endpoint for primary action",
    "Core processing function",
    "Response handling without persistence",
    "API client for submission"
  ],
  "selected_stack": {
    "scope": "backend",
    "backend": "fastapi",
    "frontend": "none",
    "apis": [
      "openrouter",
      "upstash_redis"
    ],
    "database": "none"
  }
}
```

### PRD generator input

```json
{
  "normalized": {
    "system_name": "AToolThat",
    "purpose": "Provide a concrete implementation of 'A tool that summarizes my daily notes and gives me one action plan.' for the target users.",
    "core_features": [
      "Primary user workflow",
      "Structured input validation",
      "Deterministic output formatting",
      "Basic error handling"
    ],
    "user_types": [
      "Primary user"
    ],
    "input_output": [
      "Step 1: Client sends HTTP request directly to the API",
      "Step 2: FastAPI endpoint validates request and routes to core logic",
      "Step 3: Core logic processes the request deterministically",
      "Step 4: JSON response returned (no persistence)"
    ],
    "data_model": [
      "No persistent data stored"
    ],
    "constraints": [
      "Backend selected: fastapi",
      "Frontend selected: none",
      "Database selected: none",
      "APIs selected: openrouter, upstash_redis"
    ],
    "assumptions": [
      "Assuming text-based user input only",
      "Assuming single-user concurrency",
      "Assuming no authentication unless added later"
    ],
    "unknowns": [
      "Scaling expectations not provided",
      "Latency budget unspecified"
    ],
    "selected_stack": {
      "scope": "backend",
      "backend": "fastapi",
      "frontend": "none",
      "apis": [
        "openrouter",
        "upstash_redis"
      ],
      "database": "none"
    }
  },
  "architecture": {
    "components": [
      {
        "name": "FastAPI API Layer",
        "responsibility": "Handles incoming requests and returns responses"
      },
      {
        "name": "Core Service",
        "responsibility": "Executes the main business logic"
      }
    ],
    "data_flow": [
      "Step 1: Client calls API endpoint",
      "Step 2: Core service processes the input",
      "Step 3: Results are returned to the client"
    ],
    "dependencies": [
      "API Layer calls Core Service for processing"
    ],
    "risks": [
      "Ambiguous requirements could lead to rework",
      "Scaling assumptions may need revision"
    ],
    "failure_points": [
      "API layer returns 500 if downstream LLM/logic errors"
    ],
    "minimal_mvp_components": [
      "FastAPI endpoint for primary action",
      "Core processing function",
      "Response handling without persistence",
      "API client for submission"
    ],
    "selected_stack": {
      "scope": "backend",
      "backend": "fastapi",
      "frontend": "none",
      "apis": [
        "openrouter",
        "upstash_redis"
      ],
      "database": "none"
    }
  }
}
```

### Final PRD output

```markdown
# AToolThat PRD

## Overview
This PRD defines the core workflow, users, and technical approach for the system. It focuses on delivering the primary value quickly with clear constraints.

## System Contract (Source of Truth)
- frontend_required: false

### 1. Core Entities
- **PrimaryRequest:** The user-submitted input payload that triggers processing.
- **PrimaryResult:** The structured output returned to the client.

### 2. API Contract
| Method | Path | Purpose | Input (high-level) | Output (high-level) |
|--------|------|---------|--------------------|---------------------|
| POST | /generate | Submit a request for processing | {payload: object} | {result: object} |
| GET | /health | Basic service health check | (none) | {status: string} |

### 3. Data Flow
1. User submits input via UI (if present) or an API client.
2. API Layer validates and normalizes the request.
3. Core Service executes the main workflow.
4. Optional persistence stores request/result if enabled.
5. API Layer returns a JSON response to the client.

### 4. Frontend / Backend Boundary
**Frontend Responsibilities**
- Collect user input and display results.
- Manage client-side validation and UX state.
**Backend Responsibilities**
- Validate requests, run core logic, and return responses.
- Enforce server-side rules and manage persistence if enabled.

### 5. State Model (lightweight)
**Client State**
- Current form input, loading/error flags, last result.
**Server State**
- Optional persisted requests/results and configuration.

## Architecture
The system uses a simple API + service layer, with optional persistence where required. Components are intentionally minimal to keep delivery fast and focused.

## Components
### API Layer
- **Responsibility:** Receive requests and return responses
- **Interface:** HTTP endpoints
- **Key logic:** Validation, routing, and response formatting

### Core Service
- **Responsibility:** Execute the main business workflow
- **Interface:** Internal service calls
- **Key logic:** Transformation and orchestration

## API Usage
No external APIs required.

## Database Design
No persistent storage required.

## Test Cases
| Test | Input | Expected Output | Type |
|------|-------|-----------------|------|
| Basic flow | Valid input | Successful response | unit |
| Validation | Missing field | Error response | unit |
| Edge case | Large payload | Graceful handling | integration |
| Retry | Transient issue | Successful retry | integration |
| Security | Invalid auth | Access denied | e2e |
| Performance | High load | Acceptable latency | e2e |

## Implementation Notes for Build Agents
- This PRD is a coordination layer that downstream agents will use to generate `backend_prd.md` and `frontend_prd.md`.
- The **System Contract (Source of Truth)**, especially the **API Contract**, must NOT be changed downstream.
- Implementation phases will be defined separately in each downstream PRD.

```

### Growth output (generation path completeness)

```json
{
  "good": [
    {
      "title": "Clear core flow",
      "detail": "The system focuses on a single primary workflow, reducing complexity."
    },
    {
      "title": "Constraint-aligned stack",
      "detail": "The chosen stack maps cleanly to the execution model."
    }
  ],
  "warnings": [
    {
      "title": "Assumption risk",
      "detail": "Some constraints are assumed; confirm them before scaling."
    }
  ],
  "missing": [
    {
      "title": "Monitoring",
      "detail": "Add basic logging/metrics to detect failures early."
    }
  ],
  "risk_score": 45,
  "quick_wins": [
    "Add request/response logging to FastAPI",
    "Set 30s timeout around external calls"
  ],
  "blockers": [],
  "consistency_issues": [
    "Frontend set to none but UI/Frontend elements appear in normalized output.",
    "Database set to none but persistence/database elements appear in normalized output."
  ]
}
```

### env_builder output (generation path completeness)

```text
# .env — Generated by StackLens
# REQUIRED keys must be set before running. OPTIONAL keys can be left empty.

# StackLens backend [REQUIRED]
OPENAI_API_KEY=your-openai-key-here

# External APIs
# OpenRouter API key for LLM routing [REQUIRED]
OPENROUTER_API_KEY=your-openrouter-key-here

# Upstash Redis REST URL [REQUIRED] [REQUIRED]
UPSTASH_REDIS_REST_URL=your-upstash_redis-key-here
# Upstash Redis REST token [REQUIRED] [REQUIRED]
UPSTASH_REDIS_REST_TOKEN=your-upstash_redis-key-here

```

## 3) Prompt Audit (per agent)

> Full system prompt literals are in source files; user-prompt construction is deterministic string assembly in each function.

### Recommender (`backend/pipeline/recommender.py`)
- **System prompt location:** `get_recommendation()` `system_prompt` literal.
- **User prompt construction:** `constraints_block` + `scaffold_block` + `Idea:` string.
- **Injected context:** deterministic `Decision scaffold` added before idea.
- **Findings:** contains hard stack framing (`allowed`, `preferred`, `required APIs`) that can bias architecture before model reasoning.

### Context advisor (`backend/pipeline/context_advisor.py`)
- **System prompt location:** `get_context_advice()` `system_prompt` literal.
- **User prompt construction:** `Project idea` + `Chosen stack` + formatted constraints.
- **Injected context:** deterministic post-processing URL injection (`_inject_urls`).
- **Findings:** explicit rule “When unclear, default to Render” is a built-in deployment bias.

### Option advisor (`backend/pipeline/option_advisor.py`)
- **System prompt location:** `_evaluate_option()` `system_prompt` literal.
- **User prompt construction:** project + recommended stack + constraints + target option.
- **Injected context:** `_enforce_option_rules` mutates score/why_not/limits after LLM.
- **Findings:** post-LLM rule engine can override model omissions and synthesize fallback text.

### Normalizer (`backend/pipeline/normalizer.py`)
- **System prompt location:** `normalize()` `system_prompt` literal.
- **User prompt construction:** `Idea:` + `Stack:`.
- **Injected context:** hard overwrite of `constraints`, `input_output`, `data_model`, `selected_stack` after LLM.
- **Findings:** this stage is not pure normalization; it programmatically rewrites key fields.

### Analyzer (`backend/pipeline/analyzer.py`)
- **System prompt location:** `analyze()` `system_prompt` literal.
- **User prompt construction:** full `normalized` JSON dump.
- **Injected context:** post-filtering/remapping by stack (`frontend=none`, `database=none` filters).
- **Findings:** architecture output is partly LLM, partly enforced rewrite/filter.

### PRD generator (`backend/pipeline/prd_gen.py`)
- **System prompt location:** `generate_prd()` `system_prompt` literal.
- **User prompt construction:** full normalized JSON + architecture JSON.
- **Injected context:** no post-processor in this file, but prompt itself includes internal workflow language (“downstream build agents”, “coordination layer”, “frontend_required”).
- **Findings:** prompt imposes templated structure and internal-system vocabulary by design.

### Growth (`backend/pipeline/growth.py`)
- **System prompt location:** `generate_growth_check()` `system_prompt` literal.
- **User prompt construction:** `Stack selections` + full PRD text.
- **Injected context:** adds DB warning regardless of LLM, runs consistency checks programmatically.
- **Findings:** warning list is not purely model output.

### env_builder (`backend/pipeline/env_builder.py`)
- **LLM:** none.
- **Behavior:** deterministic key injection from selected APIs/database maps.

## 4) Injection / Defaults Findings

### A. Recommender scaffold pre-decides allowed/preferred stack
- **File/function:** `backend/pipeline/recommender.py::_build_decision_scaffold`
- **Code behavior:** computes `requires_backend`, `requires_frontend`, `allowed_*`, `preferred_*`, and `required_apis`.
- **Trigger:** every recommendation call.
- **Impact:** architecture is constrained before LLM output.

### B. Required API injection (`openrouter`, `tavily`) from keyword logic
- **File/function:** `backend/pipeline/recommender.py::_build_decision_scaffold`
- **Trigger:** `ai_core` -> append `openrouter`; search keywords -> append `tavily`.
- **Impact:** APIs can appear via keyword inference, not explicit user request.

### C. Recommender hard consistency enforcement
- **File/function:** `backend/pipeline/recommender.py::_enforce_stack_consistency`
- **Trigger:** every recommender result.
- **Impact:** invalid/out-of-allowed model choices are replaced with scaffold defaults.

### D. Recommender output overwrite of API selection
- **File/function:** `backend/pipeline/recommender.py::get_recommendation`
- **Behavior:** `result['recommended']['apis'] = selected_api_ids` from registry selector.
- **Trigger:** always.
- **Impact:** model API choice is replaced by deterministic selector output.

### E. Normalizer forced field overwrite
- **File/function:** `backend/pipeline/normalizer.py::normalize`
- **Behavior:** overwrites `constraints`, `input_output`, `data_model`, filters assumptions.
- **Trigger:** always after LLM call.
- **Impact:** normalized output includes programmatic template lines even if model differs.

### F. Analyzer stack-based filtering/remapping
- **File/function:** `backend/pipeline/analyzer.py::analyze`
- **Behavior:** removes components by stack, edits first data-flow line, strips DB failure points when `database=none`.
- **Trigger:** always.
- **Impact:** architecture JSON is materially transformed post-LLM.

### G. Option advisor fallback construction
- **File/function:** `backend/pipeline/option_advisor.py::_enforce_option_rules`
- **Behavior:** clamps score/confidence; auto-fills `why_not_recommended`; adds drawbacks when needed.
- **Trigger:** every option.
- **Impact:** final option output may include non-LLM synthesized rationale text.

### H. Growth deterministic warnings and consistency checks
- **File/function:** `backend/pipeline/growth.py::generate_growth_check`
- **Behavior:** appends DB warning + programmatic `consistency_issues`.
- **Trigger:** always.
- **Impact:** growth output is mixed deterministic + LLM.

### I. Fake LLM mode introduces additional templating in this environment
- **File/function:** `backend/config.py`, `backend/llm.py`
- **Behavior:** tests/default environment can route calls to `_fake_*` responders.
- **Trigger:** `USE_FAKE_LLM=1` or pytest detection.
- **Impact:** outputs become canned/template-like regardless of live prompt quality.

### Contract Adherence Check

Reference contracts are documented in `AGENTS_Defined.md` for Recommender, Context Advisor, Option Advisor, Normalizer, Analyzer, PRD Generator, and Growth Check.

- **Recommender:** required fields present in trace output; constraint handling degrades to assumptions when constraints are empty.
- **Context advisor:** returns required architecture + deployment shape; content quality is generic under fake-LLM path.
- **Option advisor:** returns required score/confidence/benefits/drawbacks shape; post-processor enforces missing pieces.
- **Normalizer:** returns required JSON keys; stack-derived fields are programmatically overwritten after model output.
- **Analyzer:** returns required keys including `failure_points` and `minimal_mvp_components`; stack filters modify result.
- **PRD generator:** returns required markdown section structure and `frontend_required` line.
- **Growth:** returns required JSON shape and adds deterministic consistency checks.

## 5) Drift Point Identification

### First observed drift in traced run
- **Stage:** `recommender` (before PRD path starts).
- **Why:** empty constraints + scaffold keyword inference produced backend-only stack and selected APIs (`openrouter`, `upstash_redis`) not explicitly requested.
- **Evidence:** recommender output already contains pre-decided architecture and APIs.

### Additional drift events
- **Normalizer:** replaces IO/data model/constraints with stack-templated text.
- **PRD generator:** writes UI/persistence optional text even when `frontend=none` and `database=none` in inputs.

## 6) PRD Generator Root Cause Analysis

### Exact input to PRD generator
- See `prd_generator_input` JSON above (contains pre-decided stack and architecture).

### Input quality signals
- Input already includes selected stack and templated normalized constraints.
- Upstream architecture is already narrowed to stack-constrained components.

### Classification (requested A/B/C/D)
- **A) Hallucinating structure:** **Yes (minor)** — PRD includes UI/persistence wording despite `frontend=none`, `database=none`.
- **B) Expanding vague input:** **Yes (moderate)** — idea is vague and unconstrained.
- **C) Copying internal template patterns:** **Yes (high)** — prompt enforces fixed section template and internal “downstream agents” phrasing.
- **D) Reflecting earlier bad decisions:** **Yes (highest)** — PRD mostly mirrors upstream scaffolded decisions.

## 7) Context Contamination Findings

### Detected internal-language leakage in prompts
- `prd_gen.py` system prompt explicitly injects internal phrases:
  - “agent-ready PRDs”
  - “downstream build agents”
  - “coordination layer”
  - strict `frontend_required` contract line.
- This is direct prompt content, not accidental contamination.

### CodeGarden docs leakage into runtime
- No direct runtime import/injection from `docs/superpowers/*` or `AGENTS_Defined*.md` found in pipeline execution path.
- Contamination is mainly from runtime prompt text and deterministic scaffold logic, not from docs file ingestion.

## 8) Final Diagnosis (blunt split)

- **Prompt issue:** **35%**
  - PRD prompt enforces template/internal vocabulary; context/deployment prompts include built-in defaults.
- **Pipeline issue:** **45%**
  - Multi-stage deterministic rewrites and stack hardening dominate final outputs.
- **Injection/default issue:** **20%**
  - Keyword-based API/backend inference and fallback rules add unrequested architecture details.

---

### Contract adherence checkpoint (quick)
- Recommender/context/option/normalizer/analyzer/prd/growth outputs in trace contain required top-level contract fields.
- Constraint usage exists structurally, but with empty constraints the pipeline relies heavily on assumptions/default scaffolds.
- Project-specificity degrades in fake-LLM mode; outputs become generic even when contract shape is satisfied.
