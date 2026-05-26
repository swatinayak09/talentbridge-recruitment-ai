"""
TalentBridge Agentic AI Recruitment Support System
Prototype API — Pipeline Insights & Escalation/Compliance Agents
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agents.escalation_compliance import EscalationComplianceAgent
from agents.pipeline_insights import PipelineInsightsAgent

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "pipeline.json"
STATIC_DIR = ROOT / "static"

app = FastAPI(
    title="TalentBridge Recruitment Agents",
    description="Pipeline Insights & Escalation/Compliance agents for capstone prototype",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_pipeline() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TalentBridge Agents API"}


@app.get("/api/requisitions")
async def list_requisitions():
    data = load_pipeline()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "client": r.get("client"),
            "status": r.get("status"),
            "priority": r.get("priority"),
            "candidate_count": len(r.get("candidates", [])),
        }
        for r in data.get("requisitions", [])
    ]


@app.get("/api/agents/pipeline-insights")
async def pipeline_insights(
    requisition_id: str | None = Query(None, description="Filter by requisition ID"),
):
    data = load_pipeline()
    agent = PipelineInsightsAgent(data)
    return agent.run(requisition_id)


@app.get("/api/agents/escalation-compliance")
async def escalation_compliance(
    requisition_id: str | None = Query(None, description="Filter by requisition ID"),
):
    data = load_pipeline()
    agent = EscalationComplianceAgent(data)
    return agent.run(requisition_id)


@app.get("/api/agents/combined")
async def combined_report(
    requisition_id: str | None = Query(None, description="Filter by requisition ID"),
):
    data = load_pipeline()
    pipeline_agent = PipelineInsightsAgent(data)
    escalation_agent = EscalationComplianceAgent(data)
    return {
        "pipeline_insights": pipeline_agent.run(requisition_id),
        "escalation_compliance": escalation_agent.run(requisition_id),
    }


@app.get("/api/pipeline/raw")
async def raw_pipeline():
    return load_pipeline()


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
