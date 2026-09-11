import time
from typing import Any, Dict, List, Optional


class InvestigatorAgent:
    """
    Investigator Agent (INV-001)
    Analyzes detected alerts to determine:
    1. Why is this event suspicious?
    2. What specific evidence supports this assessment?
    3. What is the verified contextual risk?
    """
    def __init__(self, agent_id: str = "INV-001"):
        self.agent_id = agent_id

    def investigate(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes deep contextual investigation on a single alert.
        """
        cluster_id = alert.get("cluster_id", "C000")
        alert_id = alert.get("alert_id", "ALT-000")
        source = alert.get("source", "Generic")
        template = alert.get("template", "")
        risk = alert.get("risk", "LOW")
        risk_score = alert.get("risk_score", 0)
        confidence = alert.get("confidence", 0.85)
        count = alert.get("count", 1)
        frequency = alert.get("frequency", 0.0)
        evidence = alert.get("evidence", [])
        affected_lines = alert.get("affected_lines", [])

        # Formulate contextual reasoning based on source and patterns
        notes = []
        if frequency <= 0.10:
            notes.append(f"Event occurs at an extremely anomalous frequency of {frequency:.2f}% ({count} occurrence)")
        elif frequency <= 1.0:
            notes.append(f"Infrequent event pattern observed ({frequency:.2f}%)")

        if "authentication failure" in template.lower() or "failed" in template.lower():
            notes.append("Indicator of credential brute force or authentication anomaly")
        elif "delete" in template.lower():
            notes.append("Potentially disruptive resource deletion or data purge operation")
        elif "replicate" in template.lower() or "transfer" in template.lower():
            notes.append("Unusual data replication or lateral transfer operation")
        elif "su(pam_unix)" in template.lower() or "root" in template.lower():
            notes.append("Privilege escalation or elevated administrative session opened")
        elif "error" in template.lower():
            notes.append("System service error state detected")

        if not notes:
            notes.append("Deviation from baseline statistical frequency threshold")

        investigation_reason = f"{alert.get('reason', 'Suspicious event detected.')} Evidence confirms {len(evidence)} associated log line(s)."

        # Determine preliminary recommended action for Response Agent
        if risk in ("CRITICAL", "HIGH") or risk_score >= 60:
            recommended_action = "ESCALATE"
        elif risk == "MEDIUM" or risk_score >= 30:
            recommended_action = "MONITOR"
        elif risk_score >= 15:
            recommended_action = "LOG_AND_MONITOR"
        else:
            recommended_action = "NO_ACTION"

        return {
            "agent_id": self.agent_id,
            "alert_id": alert_id,
            "cluster_id": cluster_id,
            "source": source,
            "risk": risk,
            "risk_score": risk_score,
            "confidence": confidence,
            "status": "INVESTIGATED",
            "count": count,
            "frequency": frequency,
            "reason": investigation_reason,
            "evidence": evidence,
            "affected_lines": affected_lines,
            "investigation_notes": "; ".join(notes),
            "recommended_action": recommended_action,
            "investigated_at": time.time()
        }

    def investigate_batch(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Investigate a collection of alerts."""
        return [self.investigate(alert) for alert in alerts]
