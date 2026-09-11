import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from parser.source_detector import detect_log_source
from parser.loader import extract_timestamp, load_log_file, LogFormatError
from parser.template_miner import mine_templates
from detector.anomaly_detector import detect_cluster_anomalies
from detector.alert_engine import AlertEngine
from agents.agent_manager import AgentManager
from blockchain.ledger import load_ledger
from blockchain.verifier import verify_chain
from storage.database import get_db
from evaluation.evaluator import evaluate_system_performance


api_router = APIRouter(prefix="/api", tags=["LogLens Unified Platform"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def calculate_security_health_score(alerts: List[Dict[str, Any]], chain_valid: bool) -> Tuple[int, str]:
    """
    Dynamically computes the SOC Security Health Score (0-100) based on
    active alert counts, risk severity weights, and blockchain integrity.
    """
    base_score = 100

    if not chain_valid:
        base_score -= 40

    for a in alerts:
        risk = (a.get("risk") or "LOW").upper()
        if risk == "CRITICAL":
            base_score -= 15
        elif risk == "HIGH":
            base_score -= 8
        elif risk == "MEDIUM":
            base_score -= 3
        elif risk == "LOW":
            base_score -= 1

    health_score = max(0, min(100, base_score))

    if health_score >= 85:
        status_label = "OPTIMAL"
    elif health_score >= 70:
        status_label = "STABLE"
    elif health_score >= 50:
        status_label = "DEGRADED"
    else:
        status_label = "CRITICAL"

    return health_score, status_label


def run_pipeline_on_records(records: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """
    Runs the complete LogLens analysis pipeline on a set of structured log records:
    Templates -> Anomalies -> Alerts -> Multi-Agent -> Blockchain -> DB
    """
    if not records:
        raise LogFormatError("Log data contains zero valid records.")

    # 1. Template Mining
    templates = mine_templates(records)

    # 2. Anomaly Detection & Scoring
    anomalies = detect_cluster_anomalies(templates, records, alert_threshold=30)

    # 3. Alert Generation
    alert_engine = AlertEngine(alert_threshold=30)
    alerts = alert_engine.generate_alerts(anomalies, records, source=source)

    # 4. Multi-Agent Processing & Blockchain Commit
    agent_mgr = AgentManager()
    agent_output = agent_mgr.process_alerts(alerts, record_to_blockchain=True)

    # 5. Persist into SQLite
    db = get_db()
    db.save_analysis_run(
        logs=records,
        templates=templates,
        alerts=alerts,
        investigations=agent_output["investigations"],
        responses=agent_output["responses"],
        source=source
    )

    # 6. Calculate dynamic health score
    chain = load_ledger()
    chain_valid = verify_chain(chain)
    health_score, health_status = calculate_security_health_score(alerts, chain_valid)

    # Risk breakdown
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in alerts:
        r = (a.get("risk") or "LOW").upper()
        if r in risk_counts:
            risk_counts[r] += 1

    return {
        "status": "SUCCESS",
        "source": source,
        "total_logs": len(records),
        "total_templates": len(templates),
        "anomalies_detected": len(alerts),
        "investigations_completed": len(agent_output["investigations"]),
        "responses_formulated": len(agent_output["responses"]),
        "blockchain_blocks": len(chain),
        "blockchain_valid": chain_valid,
        "security_health_score": health_score,
        "health_status": health_status,
        "risk_distribution": risk_counts
    }


# ==========================================
# ENDPOINT 1: DASHBOARD
# ==========================================
@api_router.get("/dashboard")
def get_dashboard_summary():
    """
    Aggregated SOC Security Overview.
    Returns dynamic health score, risk distribution, alert counts, and agent activity.
    """
    db = get_db()
    alerts = db.get_alerts()
    templates = db.get_templates()
    investigations = db.get_investigations()
    responses = db.get_responses()
    blocks = db.get_blockchain_blocks()

    chain = load_ledger()
    chain_valid = verify_chain(chain)
    health_score, health_status = calculate_security_health_score(alerts, chain_valid)

    # Risk counts
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in alerts:
        r = (a.get("risk") or "LOW").upper()
        if r in risk_counts:
            risk_counts[r] += 1

    # Total logs
    _, total_logs = db.get_logs(limit=1)

    # Recent 5 alerts
    recent_alerts = alerts[:5]

    return {
        "overview": {
            "total_logs": total_logs,
            "total_templates": len(templates),
            "total_anomalies": len(alerts),
            "investigations_completed": len(investigations),
            "responses_formulated": len(responses),
            "blockchain_blocks": len(blocks) or len(chain)
        },
        "health": {
            "security_health_score": health_score,
            "status": health_status,
            "blockchain_valid": chain_valid
        },
        "risk_distribution": risk_counts,
        "recent_alerts": recent_alerts,
        "system_health": {
            "log_loader": "ONLINE",
            "preprocessor": "ONLINE",
            "template_miner": "ONLINE",
            "anomaly_engine": "ONLINE",
            "investigator_agent": "ONLINE",
            "response_agent": "ONLINE",
            "blockchain_ledger": "VERIFIED" if chain_valid else "TAMPER_DETECTED"
        }
    }


# ==========================================
# ENDPOINT 2: UPLOAD LOGS
# ==========================================
@api_router.post("/logs/upload")
async def upload_log_file(
    file: Optional[UploadFile] = File(None),
    sample_dataset: Optional[str] = Form(None)
):
    """
    Upload a log file or select a pre-loaded sample dataset (HDFS, Linux, Apache).
    Executes full pipeline: Source Detection -> Template Mining -> Anomaly Detection ->
    Multi-Agent Investigation -> Response Generation -> Blockchain Evidence Storage.
    """
    records = []
    detected_source = "Generic"

    # Option A: Pre-loaded sample requested
    if sample_dataset and sample_dataset.upper() in ("HDFS", "LINUX", "APACHE"):
        name = sample_dataset.upper()
        if name == "HDFS":
            sample_path = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
        elif name == "LINUX":
            sample_path = PROJECT_ROOT / "data" / "loghub" / "Linux" / "Linux_2k.log"
        else:
            sample_path = PROJECT_ROOT / "data" / "loghub" / "Apache" / "Apache_2k.log"

        if not sample_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sample dataset file '{sample_path.name}' not found.")

        try:
            from parser.loader import load_log_records
            records = load_log_records(sample_path)
            detected_source = records[0]["source"] if records else name
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error loading sample dataset: {str(e)}")

    # Option B: User uploaded a file
    elif file is not None:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file has no filename.")

        # Read content safely
        try:
            content_bytes = await file.read()
            text_content = content_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read upload content: {str(e)}")

        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        if not lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded log file is empty or contains only whitespace.")

        detected_source = detect_log_source(lines[:50])
        for idx, l in enumerate(lines, start=1):
            records.append({
                "line_id": idx,
                "raw_log": l,
                "source": detected_source,
                "timestamp": extract_timestamp(l, detected_source) or f"L{idx}"
            })
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a file upload or specify 'sample_dataset' (HDFS, Linux, Apache)."
        )

    # Execute analysis pipeline
    try:
        result = run_pipeline_on_records(records, detected_source)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pipeline execution error: {str(e)}")


class AnalyzeJsonRequest(BaseModel):
    sample_dataset: Optional[str] = None
    raw_logs: Optional[List[str]] = None
    log_text: Optional[str] = None


@api_router.post("/logs/analyze")
def analyze_logs_json(payload: AnalyzeJsonRequest):
    """
    JSON endpoint for log analysis. Supports specifying sample_dataset ('HDFS', 'Linux', 'Apache')
    or passing an array/text of raw log lines.
    """
    records = []
    detected_source = "Generic"

    if payload.sample_dataset and payload.sample_dataset.upper() in ("HDFS", "LINUX", "APACHE"):
        name = payload.sample_dataset.upper()
        if name == "HDFS":
            sample_path = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
        elif name == "LINUX":
            sample_path = PROJECT_ROOT / "data" / "loghub" / "Linux" / "Linux_2k.log"
        else:
            sample_path = PROJECT_ROOT / "data" / "loghub" / "Apache" / "Apache_2k.log"

        if not sample_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sample dataset file '{sample_path.name}' not found.")

        from parser.loader import load_log_records
        records = load_log_records(sample_path)
        detected_source = records[0]["source"] if records else name

    elif payload.log_text or payload.raw_logs:
        if payload.log_text:
            lines = [l.strip() for l in payload.log_text.splitlines() if l.strip()]
        else:
            lines = [str(l).strip() for l in (payload.raw_logs or []) if str(l).strip()]

        if not lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided log text or array contains no lines.")

        detected_source = detect_log_source(lines[:50])
        for idx, l in enumerate(lines, start=1):
            records.append({
                "line_id": idx,
                "raw_log": l,
                "source": detected_source,
                "timestamp": extract_timestamp(l, detected_source) or f"L{idx}"
            })
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide 'sample_dataset', 'raw_logs', or 'log_text'.")

    try:
        return run_pipeline_on_records(records, detected_source)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pipeline execution error: {str(e)}")



# ==========================================
# ENDPOINT 3: LOGS
# ==========================================
@api_router.get("/logs")
def get_logs(
    source: Optional[str] = Query(None),
    cluster_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Searchable, filterable, and paginated log explorer.
    """
    db = get_db()
    rows, total = db.get_logs(
        source=source,
        cluster_id=cluster_id,
        search=search,
        limit=limit,
        offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": rows
    }


# ==========================================
# ENDPOINT 4: TEMPLATES
# ==========================================
@api_router.get("/templates")
def get_templates():
    """
    Returns mined event templates with cluster IDs, frequencies, and counts.
    """
    db = get_db()
    templates = db.get_templates()
    return {
        "count": len(templates),
        "templates": templates
    }


# ==========================================
# ENDPOINT 5: ALERTS
# ==========================================
@api_router.get("/alerts")
def get_alerts():
    """
    Returns all detected security alerts with explainable scores and evidence.
    """
    db = get_db()
    alerts = db.get_alerts()
    return {
        "count": len(alerts),
        "alerts": alerts
    }


@api_router.get("/alerts/{alert_id}")
def get_alert_by_id(alert_id: str):
    """
    Detailed alert breakdown including evidence lines and raw log entries.
    """
    db = get_db()
    alert = db.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")
    return alert


# ==========================================
# ENDPOINT 6: INVESTIGATIONS
# ==========================================
@api_router.get("/investigations")
def get_investigations():
    """
    Returns all Investigator Agent records.
    """
    db = get_db()
    investigations = db.get_investigations()
    return {
        "count": len(investigations),
        "investigations": investigations
    }


# ==========================================
# ENDPOINT 7: RESPONSES
# ==========================================
@api_router.get("/responses")
def get_responses():
    """
    Returns all Response Agent recommendations.
    """
    db = get_db()
    responses = db.get_responses()
    return {
        "count": len(responses),
        "responses": responses
    }


# ==========================================
# ENDPOINT 8: BLOCKCHAIN
# ==========================================
@api_router.get("/blockchain")
def get_blockchain_ledger():
    """
    Returns the complete chronological tamper-evident evidence chain.
    """
    chain = load_ledger()
    blocks = [b.to_dict() for b in chain.get_chain()]
    return {
        "total_blocks": len(blocks),
        "blocks": blocks
    }


@api_router.get("/blockchain/validate")
def validate_blockchain():
    """
    Cryptographically verifies the entire SHA-256 evidence chain.
    """
    chain = load_ledger()
    is_valid = verify_chain(chain)
    return {
        "valid": is_valid,
        "total_blocks": len(chain),
        "status": "VALID" if is_valid else "TAMPER_DETECTED",
        "verified_at": time.time()
    }


# ==========================================
# ENDPOINT 9: EVALUATION
# ==========================================
@api_router.get("/evaluation")
def get_evaluation_metrics(dataset: str = Query("HDFS")):
    """
    Computes genuine system evaluation metrics:
    Precision, Recall, F1 Score, False Positive Rate, Latency, and Template Mining Accuracy.
    """
    try:
        metrics = evaluate_system_performance(dataset_name=dataset)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Evaluation calculation failed: {str(e)}")
