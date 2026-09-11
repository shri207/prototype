import time
from typing import Any, Dict, List


class ResponseAgent:
    """
    Response Agent (RESP-001)
    Maps risk assessments and investigation findings into safe, actionable,
    and auditable defensive response recommendations.
    Rules:
    - CRITICAL / HIGH -> ESCALATE (Priority: CRITICAL / HIGH)
    - MEDIUM          -> MONITOR (Priority: MEDIUM)
    - LOW             -> LOG_AND_MONITOR (Priority: LOW)
    - Others          -> NO_ACTION
    """
    def __init__(self, agent_id: str = "RESP-001"):
        self.agent_id = agent_id

    def formulate_response(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derives an operational response recommendation from investigation details.
        """
        alert_id = investigation.get("alert_id", "ALT-000")
        cluster_id = investigation.get("cluster_id", "C000")
        risk = (investigation.get("risk") or "LOW").upper()
        risk_score = investigation.get("risk_score", 0)

        if risk == "CRITICAL" or risk_score >= 80:
            action = "ESCALATE"
            priority = "CRITICAL"
            reason = f"Immediate security intervention required: Risk score {risk_score}/100 exceeds critical threshold. Forward to senior incident responder."
        elif risk == "HIGH" or risk_score >= 60:
            action = "ESCALATE"
            priority = "HIGH"
            reason = f"Elevated security review required: Risk score {risk_score}/100 with abnormal patterns detected. Queue for Tier-2 SOC analysis."
        elif risk == "MEDIUM" or risk_score >= 30:
            action = "MONITOR"
            priority = "MEDIUM"
            reason = f"Continuous telemetry observation advised: Risk score {risk_score}/100. Watch for recurrence or correlation with other anomalies."
        elif risk == "LOW" or risk_score >= 10:
            action = "LOG_AND_MONITOR"
            priority = "LOW"
            reason = f"Routine logging: Low anomaly score ({risk_score}/100). Maintain audit trail for historical baseline reference."
        else:
            action = "NO_ACTION"
            priority = "LOW"
            reason = "Standard baseline activity within normal statistical parameters. No action needed."

        response_id = f"RESP-{alert_id.replace('ALT-', '')}"

        return {
            "response_id": response_id,
            "alert_id": alert_id,
            "cluster_id": cluster_id,
            "agent_id": self.agent_id,
            "action": action,
            "priority": priority,
            "risk": risk,
            "risk_score": risk_score,
            "reason": reason,
            "approval_required": action == "ESCALATE",
            "executed": False,
            "decided_at": time.time()
        }

    def formulate_batch(self, investigations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formulate responses for a batch of investigations."""
        return [self.formulate_response(inv) for inv in investigations]
