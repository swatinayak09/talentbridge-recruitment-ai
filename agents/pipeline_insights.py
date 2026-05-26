"""
Pipeline Insights Agent
Provides hiring pipeline summaries, bottleneck analysis, aging applications,
and role-wise status updates for TalentBridge recruiters and hiring managers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


STAGE_LABELS = {
    "application_review": "Application Review",
    "phone_screen": "Phone Screen",
    "technical_interview": "Technical Interview",
    "hiring_manager_interview": "HM Interview",
    "offer": "Offer",
    "background_check": "Background Check",
    "hired": "Hired",
    "rejected": "Rejected",
}

STAGE_ORDER = list(STAGE_LABELS.keys())


class PipelineInsightsAgent:
    """Analyzes recruitment pipeline data and produces actionable insights."""

    def __init__(self, pipeline_data: dict[str, Any]) -> None:
        self.data = pipeline_data
        self.sla_days: dict[str, int] = pipeline_data.get("sla_days", {})

    def run(self, requisition_id: str | None = None) -> dict[str, Any]:
        """Generate full pipeline insight report, optionally filtered by requisition."""
        requisitions = self._filter_requisitions(requisition_id)
        all_candidates = self._flatten_candidates(requisitions)

        return {
            "agent": "Pipeline Insights Agent",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "scope": requisition_id or "all_requisitions",
            "executive_summary": self._executive_summary(requisitions, all_candidates),
            "role_wise_status": self._role_wise_status(requisitions),
            "stage_distribution": self._stage_distribution(all_candidates),
            "bottlenecks": self._detect_bottlenecks(requisitions, all_candidates),
            "aging_applications": self._aging_applications(all_candidates, requisitions),
            "priority_actions": self._priority_actions(requisitions, all_candidates),
            "metrics": self._compute_metrics(requisitions, all_candidates),
        }

    def _filter_requisitions(self, requisition_id: str | None) -> list[dict]:
        reqs = self.data.get("requisitions", [])
        if requisition_id:
            return [r for r in reqs if r["id"] == requisition_id]
        return reqs

    def _flatten_candidates(
        self, requisitions: list[dict]
    ) -> list[dict[str, Any]]:
        result = []
        for req in requisitions:
            for c in req.get("candidates", []):
                result.append({**c, "requisition_id": req["id"], "role_title": req["title"]})
        return result

    def _executive_summary(
        self, requisitions: list[dict], candidates: list[dict]
    ) -> str:
        open_roles = sum(1 for r in requisitions if r.get("status") == "open")
        on_hold = sum(1 for r in requisitions if r.get("status") == "on_hold")
        aging = sum(1 for c in candidates if "aging" in c.get("flags", []))
        high_priority = sum(1 for r in requisitions if r.get("priority") == "high")

        parts = [
            f"{len(requisitions)} active requisition(s) in scope ({open_roles} open, {on_hold} on hold).",
            f"{len(candidates)} candidate(s) across the pipeline.",
            f"{aging} application(s) exceed SLA thresholds and need attention.",
            f"{high_priority} high-priority role(s) require accelerated follow-up.",
        ]
        return " ".join(parts)

    def _role_wise_status(self, requisitions: list[dict]) -> list[dict]:
        status_list = []
        for req in requisitions:
            candidates = req.get("candidates", [])
            stages: dict[str, int] = {}
            for c in candidates:
                stage = c.get("stage", "unknown")
                stages[stage] = stages.get(stage, 0) + 1

            oldest = max(candidates, key=lambda c: c.get("days_in_stage", 0), default=None)
            status_list.append(
                {
                    "requisition_id": req["id"],
                    "title": req["title"],
                    "client": req.get("client"),
                    "status": req.get("status"),
                    "priority": req.get("priority"),
                    "recruiter": req.get("recruiter"),
                    "hiring_manager": req.get("hiring_manager"),
                    "candidate_count": len(candidates),
                    "stage_breakdown": {
                        STAGE_LABELS.get(k, k): v for k, v in stages.items()
                    },
                    "oldest_in_stage_days": oldest["days_in_stage"] if oldest else 0,
                    "health": self._role_health(req, candidates),
                }
            )
        return status_list

    def _role_health(self, req: dict, candidates: list[dict]) -> str:
        if req.get("status") == "on_hold":
            return "at_risk"
        aging_count = sum(1 for c in candidates if "aging" in c.get("flags", []))
        if aging_count >= 2 or (candidates and aging_count / len(candidates) >= 0.5):
            return "critical"
        if aging_count >= 1:
            return "watch"
        return "healthy"

    def _stage_distribution(self, candidates: list[dict]) -> dict[str, int]:
        dist: dict[str, int] = {}
        for c in candidates:
            label = STAGE_LABELS.get(c.get("stage", ""), c.get("stage", "Unknown"))
            dist[label] = dist.get(label, 0) + 1
        return dist

    def _detect_bottlenecks(
        self, requisitions: list[dict], candidates: list[dict]
    ) -> list[dict]:
        bottlenecks = []

        # Stage-level congestion
        stage_totals: dict[str, list[int]] = {}
        for c in candidates:
            stage = c.get("stage", "")
            stage_totals.setdefault(stage, []).append(c.get("days_in_stage", 0))

        for stage, days_list in stage_totals.items():
            if len(days_list) >= 2:
                avg_days = sum(days_list) / len(days_list)
                sla = self.sla_days.get(stage, 7)
                if avg_days > sla * 0.8:
                    bottlenecks.append(
                        {
                            "type": "stage_congestion",
                            "severity": "high" if avg_days > sla else "medium",
                            "stage": STAGE_LABELS.get(stage, stage),
                            "message": (
                                f"{len(days_list)} candidate(s) in {STAGE_LABELS.get(stage, stage)} "
                                f"averaging {avg_days:.1f} days (SLA: {sla} days)."
                            ),
                            "recommendation": self._stage_recommendation(stage),
                        }
                    )

        # Recruiter workload
        recruiter_load: dict[str, int] = {}
        for req in requisitions:
            rec = req.get("recruiter", "Unassigned")
            recruiter_load[rec] = recruiter_load.get(rec, 0) + len(req.get("candidates", []))

        for recruiter, count in recruiter_load.items():
            if count >= 4:
                bottlenecks.append(
                    {
                        "type": "recruiter_capacity",
                        "severity": "medium",
                        "stage": None,
                        "message": f"{recruiter} has {count} active candidates across scoped roles.",
                        "recommendation": "Consider redistributing follow-ups or prioritizing high-impact roles.",
                    }
                )

        # Stale requisitions
        for req in requisitions:
            if req.get("status") == "on_hold":
                bottlenecks.append(
                    {
                        "type": "requisition_blocked",
                        "severity": "high",
                        "stage": None,
                        "message": f"{req['title']} ({req['id']}) is on hold with candidates still in pipeline.",
                        "recommendation": "Confirm with hiring manager whether to release, reject, or re-engage candidates.",
                    }
                )

        return sorted(bottlenecks, key=lambda b: {"high": 0, "medium": 1, "low": 2}[b["severity"]])

    def _stage_recommendation(self, stage: str) -> str:
        recommendations = {
            "application_review": "Batch resume reviews or assign backup screener.",
            "phone_screen": "Send scheduling nudges and offer expanded time slots.",
            "technical_interview": "Confirm panel availability and collect feedback within 48 hours.",
            "hiring_manager_interview": "Escalate to hiring manager for overdue feedback.",
            "offer": "Route offer approvals to finance/legal if pending > 3 days.",
            "background_check": "Coordinate with compliance on open verification items.",
        }
        return recommendations.get(stage, "Review pending actions and clear blockers.")

    def _aging_applications(
        self, candidates: list[dict], requisitions: list[dict]
    ) -> list[dict]:
        req_map = {r["id"]: r for r in requisitions}
        aging = []

        for c in candidates:
            stage = c.get("stage", "")
            sla = self.sla_days.get(stage, 7)
            days = c.get("days_in_stage", 0)
            is_flagged = "aging" in c.get("flags", [])
            overdue = days > sla

            if is_flagged or overdue:
                req = req_map.get(c.get("requisition_id", ""), {})
                aging.append(
                    {
                        "candidate_id": c["id"],
                        "candidate_name": c["name"],
                        "requisition_id": c.get("requisition_id"),
                        "role_title": c.get("role_title"),
                        "stage": STAGE_LABELS.get(stage, stage),
                        "days_in_stage": days,
                        "sla_days": sla,
                        "days_over_sla": max(0, days - sla),
                        "pending_action": c.get("pending_action"),
                        "recruiter": req.get("recruiter"),
                    }
                )

        return sorted(aging, key=lambda a: a["days_over_sla"], reverse=True)

    def _priority_actions(
        self, requisitions: list[dict], candidates: list[dict]
    ) -> list[dict]:
        actions = []
        for c in candidates:
            if c.get("pending_action"):
                req = next(
                    (r for r in requisitions if r["id"] == c.get("requisition_id")),
                    {},
                )
                urgency = "high" if "aging" in c.get("flags", []) else "normal"
                if req.get("priority") == "high":
                    urgency = "high"
                actions.append(
                    {
                        "urgency": urgency,
                        "candidate_id": c["id"],
                        "candidate_name": c["name"],
                        "role_title": c.get("role_title"),
                        "action": c["pending_action"],
                        "owner": req.get("recruiter", "Unassigned"),
                    }
                )
        return sorted(actions, key=lambda a: {"high": 0, "normal": 1}[a["urgency"]])

    def _compute_metrics(
        self, requisitions: list[dict], candidates: list[dict]
    ) -> dict[str, Any]:
        if not candidates:
            return {
                "total_candidates": 0,
                "avg_days_in_stage": 0,
                "sla_breach_rate_pct": 0,
                "roles_at_risk": 0,
            }

        total_days = sum(c.get("days_in_stage", 0) for c in candidates)
        breaches = 0
        for c in candidates:
            sla = self.sla_days.get(c.get("stage", ""), 7)
            if c.get("days_in_stage", 0) > sla:
                breaches += 1

        at_risk = sum(
            1
            for r in requisitions
            if self._role_health(r, r.get("candidates", [])) in ("at_risk", "critical")
        )

        return {
            "total_candidates": len(candidates),
            "avg_days_in_stage": round(total_days / len(candidates), 1),
            "sla_breach_rate_pct": round(100 * breaches / len(candidates), 1),
            "roles_at_risk": at_risk,
            "open_requisitions": sum(1 for r in requisitions if r.get("status") == "open"),
        }
