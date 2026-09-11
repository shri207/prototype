from typing import Any, Dict, List, Optional
try:
    from .investigator_agent import InvestigatorAgent
    from .response_agent import ResponseAgent
except ImportError:
    from investigator_agent import InvestigatorAgent
    from response_agent import ResponseAgent

from blockchain.evidence_adapter import record_evidence


class AgentManager:
    """
    Agent Manager
    Coordinates the multi-agent incident lifecycle:
    Alert Ingestion -> Investigator Agent -> Response Agent -> Blockchain Ledger
    """
    def __init__(
        self,
        investigator: Optional[InvestigatorAgent] = None,
        responder: Optional[ResponseAgent] = None
    ):
        self.investigator = investigator or InvestigatorAgent()
        self.responder = responder or ResponseAgent()

    def process_alerts(
        self,
        alerts: List[Dict[str, Any]],
        record_to_blockchain: bool = True,
        ledger_path: str = "data/evidence_ledger.json"
    ) -> Dict[str, Any]:
        """
        Processes a set of security alerts through both agents and commits
        the resulting findings into the tamper-evident blockchain ledger.
        """
        investigations = []
        responses = []
        blockchain_records = []

        for alert in alerts:
            # 1. Investigator Agent investigates the alert
            inv = self.investigator.investigate(alert)
            investigations.append(inv)

            # 2. Response Agent recommends mitigation action
            resp = self.responder.formulate_response(inv)
            responses.append(resp)

            # 3. Commit to Blockchain Ledger if enabled
            if record_to_blockchain:
                # Format event contract matching Member 3 expectations
                evidence_payload = {
                    "event_id": alert.get("alert_id"),
                    "event_type": f"LOG_ANOMALY_{alert.get('cluster_id')}",
                    "cluster_id": alert.get("cluster_id"),
                    "severity": alert.get("risk", "MEDIUM"),
                    "risk_score": alert.get("risk_score"),
                    "action": resp.get("action"),
                    "priority": resp.get("priority"),
                    "source": alert.get("source"),
                    "investigator": inv.get("agent_id"),
                    "response_agent": resp.get("agent_id"),
                    "reason": inv.get("reason"),
                    "template": alert.get("template")
                }
                block = record_evidence(evidence_payload, ledger_path=ledger_path)
                blockchain_records.append(block.to_dict())

        return {
            "investigations": investigations,
            "responses": responses,
            "blockchain_records": blockchain_records,
            "total_processed": len(alerts)
        }
