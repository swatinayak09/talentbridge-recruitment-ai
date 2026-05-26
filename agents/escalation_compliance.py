"""
Escalation and Compliance Agent
Routes sensitive, ambiguous, or high-risk cases to human recruiters and
enforces fair, consistent, compliant recruitment practices.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# Rules engine for demo — maps flags and context to escalation records
ESCALATION_RULES: list[dict[str, Any]] = [
    {
        "flag": "compliance_review",
        "category": "compliance",
        "severity": "critical",
        "reason": "Background or credential verification requires compliance review.",
        "required_action": "Compliance officer must verify before proceeding.",
        "auto_hold": True,
    },
    {
        "flag": "protected_class_note",
        "category": "fairness",
        "severity": "high",
        "reason": "Candidate record contains protected-class related note — human review required.",
        "required_action": "Recruiter must confirm screening uses job-related criteria only.",
        "auto_hold": True,
    },
    {
        "flag": "offer_delay",
        "category": "operational",
        "severity": "medium",
        "reason": "Offer stage exceeds standard timeline — potential candidate loss risk.",
        "required_action": "Escalate to hiring manager and HR operations for approval chain.",
        "auto_hold": False,
    },
    {
        "flag": "feedback_pending",
        "category": "process",
        "severity": "medium",
        "reason": "Interviewer or hiring manager feedback overdue beyond SLA.",
        "required_action": "Notify hiring manager; document delay in audit log.",
        "auto_hold": False,
    },
    {
        "flag": "stale_requisition",
        "category": "governance",
        "severity": "high",
        "reason": "Requisition on hold with active candidates — governance review needed.",
        "required_action": "Talent acquisition lead must approve candidate disposition.",
        "auto_hold": True,
    },
]

SCORE_ANOMALY_THRESHOLD = 25  # Point gap triggering ambiguous case review


class EscalationComplianceAgent:
    """Evaluates pipeline for compliance risks and generates escalation queue."""

    def __init__(self, pipeline_data: dict[str, Any]) -> None:
        self.data = pipeline_data
        self.policies = pipeline_data.get("compliance_policies", [])

    def run(self, requisition_id: str | None = None) -> dict[str, Any]:
        requisitions = self._filter_requisitions(requisition_id)
        escalations = self._build_escalation_queue(requisitions)
        fairness_checks = self._run_fairness_checks(requisitions)
        audit_recommendations = self._audit_recommendations(escalations, fairness_checks)

        return {
            "agent": "Escalation and Compliance Agent",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "scope": requisition_id or "all_requisitions",
            "summary": self._compliance_summary(escalations, fairness_checks),
            "escalation_queue": escalations,
            "fairness_checks": fairness_checks,
            "policy_reminders": self._policy_reminders(escalations),
            "audit_recommendations": audit_recommendations,
            "metrics": {
                "total_escalations": len(escalations),
                "critical_count": sum(1 for e in escalations if e["severity"] == "critical"),
                "high_count": sum(1 for e in escalations if e["severity"] == "high"),
                "on_hold_count": sum(1 for e in escalations if e.get("auto_hold")),
                "fairness_warnings": len(fairness_checks),
            },
        }

    def _filter_requisitions(self, requisition_id: str | None) -> list[dict]:
        reqs = self.data.get("requisitions", [])
        if requisition_id:
            return [r for r in reqs if r["id"] == requisition_id]
        return reqs

    def _build_escalation_queue(self, requisitions: list[dict]) -> list[dict]:
        queue: list[dict] = []
        escalation_id = 1

        for req in requisitions:
            candidates = req.get("candidates", [])
            scores = [c.get("score", 0) for c in candidates if c.get("score")]

            for candidate in candidates:
                flags = candidate.get("flags", [])

                for rule in ESCALATION_RULES:
                    if rule["flag"] in flags:
                        queue.append(
                            self._escalation_record(
                                escalation_id,
                                req,
                                candidate,
                                rule,
                            )
                        )
                        escalation_id += 1

                # Score anomaly: large gap vs role average
                if scores and candidate.get("score") is not None:
                    avg = sum(scores) / len(scores)
                    gap = abs(candidate["score"] - avg)
                    if gap >= SCORE_ANOMALY_THRESHOLD and len(candidates) > 1:
                        queue.append(
                            {
                                "id": f"ESC-{escalation_id:04d}",
                                "severity": "medium",
                                "category": "ambiguous",
                                "status": "pending_human_review",
                                "auto_hold": False,
                                "requisition_id": req["id"],
                                "role_title": req["title"],
                                "candidate_id": candidate["id"],
                                "candidate_name": candidate["name"],
                                "assigned_recruiter": req.get("recruiter"),
                                "reason": (
                                    f"Score ({candidate['score']}) deviates significantly from "
                                    f"role average ({avg:.0f}) — ambiguous fit."
                                ),
                                "required_action": (
                                    "Recruiter must document rationale before advancing or rejecting."
                                ),
                                "policy_refs": ["POL-004"],
                                "confidence": 0.72,
                            }
                        )
                        escalation_id += 1

                # Offer / background stage always gets compliance touchpoint
                stage = candidate.get("stage", "")
                if stage in ("offer", "background_check") and not any(
                    e["candidate_id"] == candidate["id"] and e["category"] == "compliance"
                    for e in queue
                ):
                    queue.append(
                        {
                            "id": f"ESC-{escalation_id:04d}",
                            "severity": "low",
                            "category": "compliance",
                            "status": "monitoring",
                            "auto_hold": False,
                            "requisition_id": req["id"],
                            "role_title": req["title"],
                            "candidate_id": candidate["id"],
                            "candidate_name": candidate["name"],
                            "assigned_recruiter": req.get("recruiter"),
                            "reason": f"Candidate in {stage.replace('_', ' ')} — ensure adverse action policy if applicable.",
                            "required_action": "Confirm documentation per POL-002 before final decision.",
                            "policy_refs": ["POL-002"],
                            "confidence": 0.95,
                        }
                    )
                    escalation_id += 1

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(queue, key=lambda e: severity_order[e["severity"]])

    def _escalation_record(
        self,
        escalation_id: int,
        req: dict,
        candidate: dict,
        rule: dict,
    ) -> dict:
        return {
            "id": f"ESC-{escalation_id:04d}",
            "severity": rule["severity"],
            "category": rule["category"],
            "status": "pending_human_review",
            "auto_hold": rule.get("auto_hold", False),
            "requisition_id": req["id"],
            "role_title": req["title"],
            "candidate_id": candidate["id"],
            "candidate_name": candidate["name"],
            "assigned_recruiter": req.get("recruiter"),
            "reason": rule["reason"],
            "required_action": rule["required_action"],
            "policy_refs": self._policy_refs_for_category(rule["category"]),
            "confidence": 0.88 if rule["severity"] == "critical" else 0.8,
        }

    def _policy_refs_for_category(self, category: str) -> list[str]:
        mapping = {
            "compliance": ["POL-002", "POL-003"],
            "fairness": ["POL-001", "POL-004"],
            "governance": ["POL-004"],
            "operational": ["POL-004"],
            "process": ["POL-004"],
            "ambiguous": ["POL-004"],
        }
        return mapping.get(category, ["POL-004"])

    def _run_fairness_checks(self, requisitions: list[dict]) -> list[dict]:
        checks = []
        for req in requisitions:
            candidates = req.get("candidates", [])
            if len(candidates) < 2:
                continue

            scores = [c["score"] for c in candidates if c.get("score") is not None]
            stages = [c["stage"] for c in candidates]

            # Check: all candidates stuck at same stage might indicate process issue
            if len(set(stages)) == 1 and len(candidates) >= 2:
                checks.append(
                    {
                        "requisition_id": req["id"],
                        "role_title": req["title"],
                        "check_type": "process_uniformity",
                        "status": "warning",
                        "message": (
                            "All candidates at same stage — verify consistent evaluation criteria applied."
                        ),
                    }
                )

            # Check: wide score spread without stage progression
            if scores and max(scores) - min(scores) > 30:
                advanced = [c for c in candidates if c["stage"] not in ("application_review", "rejected")]
                low_scored_advanced = [
                    c for c in advanced if c.get("score", 100) < min(scores) + 10
                ]
                if low_scored_advanced:
                    checks.append(
                        {
                            "requisition_id": req["id"],
                            "role_title": req["title"],
                            "check_type": "score_stage_consistency",
                            "status": "review",
                            "message": (
                                "Lower-scored candidate(s) advanced while higher scores remain behind — "
                                "confirm job-related justification is documented."
                            ),
                        }
                    )

        return checks

    def _policy_reminders(self, escalations: list[dict]) -> list[dict]:
        referenced = set()
        for e in escalations:
            referenced.update(e.get("policy_refs", []))

        reminders = []
        for policy in self.policies:
            if policy["id"] in referenced or not referenced:
                reminders.append(
                    {
                        "id": policy["id"],
                        "title": policy["title"],
                        "description": policy["description"],
                        "active": policy["id"] in referenced,
                    }
                )
        return reminders

    def _audit_recommendations(
        self, escalations: list[dict], fairness_checks: list[dict]
    ) -> list[str]:
        recs = []
        critical = [e for e in escalations if e["severity"] == "critical"]
        if critical:
            recs.append(
                f"Immediately assign {len(critical)} critical case(s) to compliance or senior recruiter."
            )
        on_hold = [e for e in escalations if e.get("auto_hold")]
        if on_hold:
            recs.append(
                f"Pause automated advancement for {len(on_hold)} candidate(s) until human review completes."
            )
        if fairness_checks:
            recs.append(
                "Log fairness check outcomes in audit trail before next pipeline movement."
            )
        if not recs:
            recs.append("No immediate compliance escalations — continue standard monitoring.")
        return recs

    def _compliance_summary(
        self, escalations: list[dict], fairness_checks: list[dict]
    ) -> str:
        critical = sum(1 for e in escalations if e["severity"] == "critical")
        high = sum(1 for e in escalations if e["severity"] == "high")
        holds = sum(1 for e in escalations if e.get("auto_hold"))

        return (
            f"{len(escalations)} case(s) queued for human review "
            f"({critical} critical, {high} high priority). "
            f"{holds} candidate(s) flagged for auto-hold pending approval. "
            f"{len(fairness_checks)} fairness check(s) require documentation."
        )
