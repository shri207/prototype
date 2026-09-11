from typing import Any, Dict, List, Optional
try:
    from .scoring_engine import evaluate_cluster_risk
except ImportError:
    from scoring_engine import evaluate_cluster_risk


class AnomalyDetector:
    """
    Evaluates mined log clusters using multi-factor explainable scoring.
    Identifies anomalous or suspicious clusters requiring investigation.
    """
    def __init__(self, alert_threshold: int = 30):
        self.alert_threshold = alert_threshold

    def detect_anomalies(
        self,
        templates: List[Dict[str, Any]],
        logs: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes mined templates, scores risk, and filters anomalies
        exceeding the threshold.
        """
        scored_clusters = []

        # Index raw logs by line_id if available
        log_by_line = {}
        if logs:
            for idx, l in enumerate(logs, start=1):
                if isinstance(l, dict):
                    line_id = l.get("line_id", idx)
                    raw = l.get("raw_log", "")
                else:
                    line_id = idx
                    raw = str(l)
                log_by_line[line_id] = raw

        for cluster in templates:
            sample_lines = cluster.get("sample_lines", [])
            raw_samples = [log_by_line.get(lid, "") for lid in sample_lines if lid in log_by_line]

            evaluation = evaluate_cluster_risk(cluster, raw_samples=raw_samples)

            anomaly_record = {
                "cluster_id": cluster.get("cluster_id"),
                "template": cluster.get("template"),
                "count": cluster.get("count", cluster.get("size", 0)),
                "frequency": cluster.get("frequency", 0.0),
                "risk": evaluation["risk"],
                "risk_score": evaluation["risk_score"],
                "confidence": evaluation["confidence"],
                "breakdown": evaluation["breakdown"],
                "explanations": evaluation["explanations"],
                "reason": evaluation["reason"],
                "sample_lines": sample_lines,
                "raw_samples": raw_samples,
                "is_anomaly": evaluation["risk_score"] >= self.alert_threshold
            }
            scored_clusters.append(anomaly_record)

        # Sort by risk score descending
        scored_clusters.sort(key=lambda x: x["risk_score"], reverse=True)
        return scored_clusters


def detect_cluster_anomalies(
    templates: List[Dict[str, Any]],
    logs: Optional[List[Any]] = None,
    alert_threshold: int = 30
) -> List[Dict[str, Any]]:
    """Convenience helper to run anomaly detector."""
    detector = AnomalyDetector(alert_threshold=alert_threshold)
    return detector.detect_anomalies(templates, logs)
