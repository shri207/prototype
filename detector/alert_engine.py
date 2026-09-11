import time
from typing import Any, Dict, List, Optional
try:
    from .anomaly_detector import detect_cluster_anomalies
except ImportError:
    from anomaly_detector import detect_cluster_anomalies


class AlertEngine:
    """
    Generates structured, evidence-backed security alerts from detected anomalies.
    Ensures every alert includes precise line references, raw log snippets,
    explainable scoring breakdown, and justification.
    """
    def __init__(self, alert_threshold: int = 30):
        self.alert_threshold = alert_threshold

    def generate_alerts(
        self,
        anomalies: List[Dict[str, Any]],
        logs: Optional[List[Any]] = None,
        source: str = "Generic"
    ) -> List[Dict[str, Any]]:
        """
        Transforms anomalous clusters into structured security alerts.
        """
        log_by_line = {}
        if logs:
            for idx, l in enumerate(logs, start=1):
                if isinstance(l, dict):
                    line_id = l.get("line_id", idx)
                    raw = l.get("raw_log", "")
                    ts = l.get("timestamp", "")
                    src = l.get("source", source)
                else:
                    line_id = idx
                    raw = str(l)
                    ts = f"L{line_id}"
                    src = source
                log_by_line[line_id] = {"raw_log": raw, "timestamp": ts, "source": src}

        alerts = []
        alert_index = 1

        for item in anomalies:
            # Only generate alerts for clusters exceeding the alert threshold
            if not item.get("is_anomaly", item.get("risk_score", 0) >= self.alert_threshold):
                continue

            sample_lines = item.get("sample_lines", [])
            evidence = []
            for lid in sample_lines:
                rec = log_by_line.get(lid, {"raw_log": "", "timestamp": f"L{lid}", "source": source})
                evidence.append({
                    "line_id": lid,
                    "raw_log": rec["raw_log"],
                    "timestamp": rec["timestamp"]
                })

            alert_id = f"ALT-{alert_index:03d}"
            alerts.append({
                "alert_id": alert_id,
                "cluster_id": item.get("cluster_id"),
                "source": source,
                "template": item.get("template"),
                "risk": item.get("risk"),
                "risk_score": item.get("risk_score"),
                "confidence": item.get("confidence", 0.90),
                "count": item.get("count", 1),
                "frequency": item.get("frequency", 0.0),
                "breakdown": item.get("breakdown", {}),
                "evidence": evidence,
                "affected_lines": sample_lines,
                "reason": item.get("reason", "Anomalous event pattern detected requiring investigation."),
                "created_at": time.time()
            })
            alert_index += 1

        return alerts


def generate_security_alerts(
    templates: List[Dict[str, Any]],
    logs: Optional[List[Any]] = None,
    source: str = "Generic",
    alert_threshold: int = 30
) -> List[Dict[str, Any]]:
    """Convenience helper to run anomaly detector and alert engine end-to-end."""
    anomalies = detect_cluster_anomalies(templates, logs, alert_threshold=alert_threshold)
    engine = AlertEngine(alert_threshold=alert_threshold)
    return engine.generate_alerts(anomalies, logs, source=source)
