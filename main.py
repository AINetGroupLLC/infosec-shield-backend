"""AI Net Shield deterministic assessment API.

The public WordPress experience scores answers inside the visitor's browser.
This API remains available for controlled integrations and preserves the
original ten-answer endpoint during the product transition.
"""

from __future__ import annotations

import os
from enum import StrEnum
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

VERSION = "2.0.0"
DEFAULT_ORIGINS = (
    "https://www.ainetstrategies.com",
    "https://ainetstrategies.com",
)

DOMAINS: dict[str, str] = {
    "strategy": "Business Direction and Value",
    "systems": "Data and Systems Readiness",
    "security": "Security and Information Protection",
    "governance": "AI Governance and Human Authority",
    "operations": "Operational Resilience",
    "delivery": "Delivery and Measurement",
}

QUESTION_DOMAINS: dict[str, str] = {
    "strategy-outcomes": "strategy",
    "strategy-prioritization": "strategy",
    "strategy-measures": "strategy",
    "strategy-economics": "strategy",
    "systems-inventory": "systems",
    "systems-data": "systems",
    "systems-legacy": "systems",
    "systems-portability": "systems",
    "security-identity": "security",
    "security-data": "security",
    "security-hygiene": "security",
    "security-recovery": "security",
    "governance-policy": "governance",
    "governance-oversight": "governance",
    "governance-inventory": "governance",
    "governance-evaluation": "governance",
    "operations-ownership": "operations",
    "operations-change": "operations",
    "operations-continuity": "operations",
    "operations-vendors": "operations",
    "delivery-workforce": "delivery",
    "delivery-acceptance": "delivery",
    "delivery-benefits": "delivery",
    "delivery-roadmap": "delivery",
}

PRIORITY_ACTIONS: dict[str, str] = {
    "strategy-outcomes": "Define the business decision, intended outcome, accountable owner, and authority.",
    "strategy-prioritization": "Compare use cases by value, feasibility, risk, dependencies, and time to evidence.",
    "strategy-measures": "Assign baselines, target measures, review dates, and stopping criteria.",
    "strategy-economics": "Build a lifecycle economic model covering implementation, operations, oversight, and exit.",
    "systems-inventory": "Inventory critical systems, data flows, interfaces, owners, and dependencies.",
    "systems-data": "Assign data ownership and document quality, access, retention, and permitted use.",
    "systems-legacy": "Select an evidence-based integration, modernization, replacement, or retirement path.",
    "systems-portability": "Define interoperability, export, fallback, and concentration-risk requirements.",
    "security-identity": "Strengthen authentication, least privilege, privileged access, and access reviews.",
    "security-data": "Apply lifecycle protection to sensitive data, credentials, prompts, outputs, and logs.",
    "security-hygiene": "Establish measurable vulnerability, patch, configuration, dependency, and exposure controls.",
    "security-recovery": "Test incident response, protected backups, restoration, and continuity.",
    "governance-policy": "Approve an AI policy covering permitted use, prohibited data, accountability, and exceptions.",
    "governance-oversight": "Define human review, escalation, override, and shutdown authority by consequence.",
    "governance-inventory": "Maintain an AI register with purpose, owner, provider, data, autonomy, and risk tier.",
    "governance-evaluation": "Evaluate before release and monitor quality, security, drift, misuse, and incidents.",
    "operations-ownership": "Assign service ownership and document runbooks, support, dependencies, and escalation.",
    "operations-change": "Use staged change control with observability, rollback, and verification.",
    "operations-continuity": "Tie capacity, performance, availability, cost, and continuity thresholds to requirements.",
    "operations-vendors": "Review third parties for security, data use, subprocessors, continuity, and exit.",
    "delivery-workforce": "Map role impacts and provide training, workflow ownership, and adoption support.",
    "delivery-acceptance": "Tie pilots to real processes with acceptance, safety, handoff, and exit criteria.",
    "delivery-benefits": "Assign benefit ownership and review outcomes, unintended effects, and corrective actions.",
    "delivery-roadmap": "Sequence milestones, resources, dependencies, review gates, and completion evidence.",
}


class AnswerValue(StrEnum):
    ESTABLISHED = "established"
    PARTIAL = "partial"
    PLANNED = "planned"
    NOT_STARTED = "not-started"
    NOT_APPLICABLE = "not-applicable"


ANSWER_SCORES: dict[AnswerValue, int | None] = {
    AnswerValue.ESTABLISHED: 4,
    AnswerValue.PARTIAL: 2,
    AnswerValue.PLANNED: 1,
    AnswerValue.NOT_STARTED: 0,
    AnswerValue.NOT_APPLICABLE: None,
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LegacyShieldRequest(StrictModel):
    answers: Annotated[list[bool], Field(min_length=10, max_length=10)]


class LegacyShieldResponse(StrictModel):
    score: int
    title: str
    summary: str
    recommendations: list[str]


class AssessmentRequest(StrictModel):
    answers: dict[str, AnswerValue]

    @field_validator("answers")
    @classmethod
    def require_complete_catalog(
        cls, answers: dict[str, AnswerValue]
    ) -> dict[str, AnswerValue]:
        expected = set(QUESTION_DOMAINS)
        provided = set(answers)
        missing = sorted(expected - provided)
        unknown = sorted(provided - expected)
        if missing or unknown:
            raise ValueError(
                f"Assessment must contain the current 24-question catalog; "
                f"missing={missing}, unknown={unknown}"
            )
        return answers


class DomainResult(StrictModel):
    id: str
    name: str
    score: int | None
    applicable: int


class PriorityResult(StrictModel):
    question_id: str
    domain: str
    reported_condition: AnswerValue
    action: str


class PathResult(StrictModel):
    label: str
    title: str
    description: str


class AssessmentResponse(StrictModel):
    version: Literal["2.0.0"] = VERSION
    score: int
    maturity: str
    summary: str
    domains: list[DomainResult]
    priorities: list[PriorityResult]
    recommended_path: PathResult
    disclaimer: str


def _allowed_origins() -> list[str]:
    configured = os.environ.get("ALLOWED_ORIGINS", "")
    values = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    return values or list(DEFAULT_ORIGINS)


def _rounded_score(total: int, maximum: int) -> int:
    if maximum <= 0:
        return 0
    return max(0, min(100, round((total / maximum) * 100)))


def _maturity(score: int) -> tuple[str, str]:
    if score >= 85:
        return (
            "Evidence-Led Execution",
            "The reported foundation is comparatively strong. Validate the evidence and continue disciplined improvement.",
        )
    if score >= 70:
        return (
            "Controlled Readiness",
            "A credible foundation is reported, with material controls or delivery dependencies still requiring closure.",
        )
    if score >= 50:
        return (
            "Developing Foundation",
            "Useful practices are reported, but uneven evidence and operating controls could weaken reliable execution.",
        )
    return (
        "Foundational Action Required",
        "Clearer ownership, evidence, and baseline controls are needed before material AI expansion or system change.",
    )


def _recommended_path(score: int, domain_scores: dict[str, int | None]) -> PathResult:
    strategy = domain_scores.get("strategy") or 0
    governance = domain_scores.get("governance") or 0
    operating_scores = [
        domain_scores.get(domain) or 0
        for domain in ("systems", "security", "operations", "delivery")
    ]

    if score < 70 or strategy < 65 or governance < 65:
        return PathResult(
            label="Path One: Advisory Services",
            title="Clarify the executive decision before implementation.",
            description=(
                "Define business outcomes, decision authority, risk boundaries, "
                "operating requirements, and an implementation-ready AI Business Strategy."
            ),
        )
    if min(operating_scores) < 75:
        return PathResult(
            label="Path Two: Selected Services",
            title="Close the operating gaps through a controlled scope.",
            description=(
                "Use the targeted readiness, implementation, governance, continuity, "
                "or managed-support service required by the weakest operating domain."
            ),
        )
    return PathResult(
        label="Executive Optimization Review",
        title="Protect the foundation and identify the next justified advantage.",
        description=(
            "Validate reported evidence, stress-test assumptions, and prioritize "
            "the next measurable opportunity without weakening control."
        ),
    )


def analyze_current(request: AssessmentRequest) -> AssessmentResponse:
    domain_results: list[DomainResult] = []
    domain_scores: dict[str, int | None] = {}

    for domain_id, domain_name in DOMAINS.items():
        question_ids = [
            question_id
            for question_id, question_domain in QUESTION_DOMAINS.items()
            if question_domain == domain_id
        ]
        scores = [
            ANSWER_SCORES[request.answers[question_id]]
            for question_id in question_ids
            if ANSWER_SCORES[request.answers[question_id]] is not None
        ]
        domain_score = (
            _rounded_score(sum(scores), len(scores) * 4) if scores else None
        )
        domain_scores[domain_id] = domain_score
        domain_results.append(
            DomainResult(
                id=domain_id,
                name=domain_name,
                score=domain_score,
                applicable=len(scores),
            )
        )

    scored_domains = [score for score in domain_scores.values() if score is not None]
    overall_score = (
        round(sum(scored_domains) / len(scored_domains)) if scored_domains else 0
    )
    maturity, summary = _maturity(overall_score)

    priority_ids = sorted(
        (
            question_id
            for question_id, value in request.answers.items()
            if ANSWER_SCORES[value] is not None and ANSWER_SCORES[value] < 4
        ),
        key=lambda question_id: (
            ANSWER_SCORES[request.answers[question_id]],
            domain_scores[QUESTION_DOMAINS[question_id]] or 0,
            question_id,
        ),
    )[:5]

    priorities = [
        PriorityResult(
            question_id=question_id,
            domain=DOMAINS[QUESTION_DOMAINS[question_id]],
            reported_condition=request.answers[question_id],
            action=PRIORITY_ACTIONS[question_id],
        )
        for question_id in priority_ids
    ]

    return AssessmentResponse(
        score=overall_score,
        maturity=maturity,
        summary=summary,
        domains=domain_results,
        priorities=priorities,
        recommended_path=_recommended_path(overall_score, domain_scores),
        disclaimer=(
            "Directional result based on self-reported conditions. It is not a "
            "certification, audit, vulnerability scan, legal opinion, or assurance."
        ),
    )


def analyze_legacy(request: LegacyShieldRequest) -> LegacyShieldResponse:
    score = sum(request.answers) * 10
    maturity, summary = _maturity(score)
    recommendations = [
        "Validate the reported answers against current evidence and accountable ownership.",
        "Review business value, systems, information security, AI governance, resilience, and delivery as connected domains.",
        "Begin with a qualified inquiry before relying on this directional result for an investment or implementation decision.",
    ]
    return LegacyShieldResponse(
        score=score,
        title=maturity,
        summary=summary,
        recommendations=recommendations,
    )


app = FastAPI(
    title="AI Net Shield API",
    description=(
        "Deterministic, non-generative readiness scoring for controlled AI Net Shield integrations."
    ),
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    max_age=3600,
)


@app.middleware("http")
async def enforce_request_limits_and_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 32_768:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body exceeds the 32 KB limit."},
        )

    response = await call_next(request)
    response.headers["Cache-Control"] = (
        "public, max-age=60" if request.url.path in {"/", "/health"} else "no-store"
    )
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/")
def read_root():
    return {
        "service": "AI Net Shield API",
        "version": VERSION,
        "status": "ready",
        "data_retention": "Assessment responses are not persisted.",
    }


@app.get("/health")
def read_health():
    return {"status": "ok", "version": VERSION}


@app.post("/analyze", response_model=LegacyShieldResponse)
def analyze_security(request: LegacyShieldRequest):
    """Compatibility endpoint for the original ten-answer application."""

    return analyze_legacy(request)


@app.post("/v2/analyze", response_model=AssessmentResponse)
def analyze_readiness(request: AssessmentRequest):
    """Score the current 24-control assessment without generative inference."""

    return analyze_current(request)
