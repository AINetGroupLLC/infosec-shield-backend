from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
origins = [
    "*"  # Allows all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ShieldRequest(BaseModel):
    answers: List[bool]

class ShieldResponse(BaseModel):
    score: int
    title: str
    summary: str
    recommendations: List[str]

@app.get("/")
def read_root():
    return {"message": "AI Net InfoSec Shield Backend is running."}

@app.post("/analyze", response_model=ShieldResponse)
def analyze_security(request: ShieldRequest):
    """
    Analyzes the user's answers to the 10-point questionnaire, calculates a score,
    and returns a tiered set of recommendations.
    """
    score = sum(1 for answer in request.answers if answer) * 10

    if score >= 80:
        title = "Strong Security & AI Posture"
        summary = "Your organization demonstrates a strong commitment to modern security principles and AI readiness. Your foundational practices are solid, positioning you well for future growth."
        recommendations = [
            "Recommendation: Consider a 'Strategic Growth Audit' to leverage your strong posture for market leadership.",
            "Recommendation: Explore advanced AI integrations to further optimize your operations.",
            "Recommendation: Solidify your position with our 'Ethical AGI Roadmap' service."
        ]
    elif score >= 50:
        title = "Good Foundation with Room for Improvement"
        summary = "Your organization has several good security and data management practices in place, but there are key areas that require attention to mitigate risks associated with legacy systems and the evolving AI landscape."
        recommendations = [
            "Recommendation: Prioritize a 'Compliance and Risk Assessment' to identify and close critical gaps.",
            "Recommendation: Our 'Legacy System Modernization' roadmap can help you securely bridge the gap to modern, AI-powered infrastructure.",
            "Recommendation: Book a consultation to see how the AI Net InfoSec Shield can provide deeper insights."
        ]
    else:
        title = "Critical Risks Identified"
        summary = "Your assessment indicates critical gaps in your security, compliance, and AI readiness posture. Immediate action is recommended to protect your assets and ensure you are not falling behind in the AI era."
        recommendations = [
            "Recommendation: An urgent 'Full Spectrum Security & Compliance Audit' is highly recommended.",
            "Recommendation: Our services can help you immediately establish foundational policies for data governance, AI usage, and incident response.",
            "Recommendation: Contact us for an emergency consultation to formulate a remediation plan."
        ]

    return ShieldResponse(
        score=score,
        title=title,
        summary=summary,
        recommendations=recommendations
    )
