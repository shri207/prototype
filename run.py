import argparse
import os
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from parser.loader import load_log_records
from parser.source_detector import detect_log_source
from parser.template_miner import mine_templates
from detector.anomaly_detector import detect_cluster_anomalies
from detector.alert_engine import AlertEngine
from agents.agent_manager import AgentManager
from blockchain.ledger import load_ledger
from blockchain.verifier import verify_chain
from storage.database import get_db
from evaluation.evaluator import evaluate_system_performance


def run_pipeline(
    dataset_name: str = "HDFS",
    log_file: str = None,
    save_to_db: bool = True
):
    """
    Executes the end-to-end LogLens pipeline:
    Log Input -> Source Detection -> Loader -> Preprocessor -> Template Miner ->
    Anomaly Detector -> Alert Engine -> Multi-Agent Investigation -> Response Agent ->
    Blockchain Ledger -> SQLite DB -> System Evaluation.
    """
    if not log_file:
        if dataset_name.upper() == "HDFS":
            log_file = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
            ground_truth_file = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log_structured.csv"
        elif dataset_name.upper() == "LINUX":
            log_file = PROJECT_ROOT / "data" / "loghub" / "Linux" / "Linux_2k.log"
            ground_truth_file = PROJECT_ROOT / "data" / "loghub" / "Linux" / "Linux_2k.log_structured.csv"
        elif dataset_name.upper() == "APACHE":
            log_file = PROJECT_ROOT / "data" / "loghub" / "Apache" / "Apache_2k.log"
            ground_truth_file = PROJECT_ROOT / "data" / "loghub" / "Apache" / "Apache_2k.log_structured.csv"
        else:
            log_file = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
            ground_truth_file = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log_structured.csv"
    else:
        log_file = Path(log_file)
        ground_truth_file = None

    print("\n" + "=" * 60)
    print("                     LOGLENS")
    print("  AI-Assisted Multi-Agent Cybersecurity Log Analysis")
    print("=" * 60)
    print(f"Log File Input   : {log_file}")

    # 1. Source Detection & Loading
    detected_source = detect_log_source(log_file)
    records = load_log_records(log_file)
    total_logs = len(records)
    print(f"Detected Source  : {detected_source}")
    print(f"Total Logs Loaded: {total_logs}")

    # 2. Template Mining
    templates = mine_templates(records)
    print(f"Templates Mined  : {len(templates)}")

    # 3. Anomaly Detection & Scoring
    anomalies = detect_cluster_anomalies(templates, records, alert_threshold=30)
    alert_engine = AlertEngine(alert_threshold=30)
    alerts = alert_engine.generate_alerts(anomalies, records, source=detected_source)
    print(f"Anomalies Found  : {len(alerts)}")

    # 4. Multi-Agent Investigation & Response
    agent_mgr = AgentManager()
    agent_output = agent_mgr.process_alerts(alerts, record_to_blockchain=True)
    investigations = agent_output["investigations"]
    responses = agent_output["responses"]
    print(f"Investigated     : {len(investigations)} (by Investigator Agent INV-001)")
    print(f"Responses Formed : {len(responses)} (by Response Agent RESP-001)")

    # 5. Blockchain Ledger Status
    chain = load_ledger()
    chain_valid = verify_chain(chain)
    total_blocks = len(chain)
    print(f"Blockchain Blocks: {total_blocks}")
    print(f"Chain Integrity  : {'VALID' if chain_valid else 'TAMPER_DETECTED'} (100% SHA-256 Verified)")

    # 6. Persistence
    if save_to_db:
        db = get_db()
        db.save_analysis_run(
            logs=records,
            templates=templates,
            alerts=alerts,
            investigations=investigations,
            responses=responses,
            source=detected_source
        )

    # 7. Dynamic Security Health Score Calculation
    base_score = 100
    if not chain_valid:
        base_score -= 40
    for a in alerts:
        r = (a.get("risk") or "LOW").upper()
        if r == "CRITICAL":
            base_score -= 15
        elif r == "HIGH":
            base_score -= 8
        elif r == "MEDIUM":
            base_score -= 3
        elif r == "LOW":
            base_score -= 1
    health_score = max(0, min(100, base_score))

    # Risk distribution
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in alerts:
        r = (a.get("risk") or "LOW").upper()
        if r in risk_counts:
            risk_counts[r] += 1

    # 8. Evaluation Metrics
    eval_res = evaluate_system_performance(
        dataset_name=detected_source,
        log_file=str(log_file),
        ground_truth_file=str(ground_truth_file) if ground_truth_file and ground_truth_file.exists() else None
    )

    # Print Final Summary Display
    print("\n" + "-" * 60)
    print("                 PIPELINE EXECUTION SUMMARY")
    print("-" * 60)
    print(f"Total Logs            : {total_logs}")
    print(f"Templates             : {len(templates)}")
    print(f"Anomalies             : {len(alerts)}")
    print(f"Investigated          : {len(investigations)}")
    print(f"Responses             : {len(responses)}")
    print(f"Blockchain Blocks     : {total_blocks}")
    print(f"Security Health Score : {health_score}/100")
    print("\nRisk Distribution:")
    print(f"  - CRITICAL          : {risk_counts['CRITICAL']}")
    print(f"  - HIGH              : {risk_counts['HIGH']}")
    print(f"  - MEDIUM            : {risk_counts['MEDIUM']}")
    print(f"  - LOW               : {risk_counts['LOW']}")

    print("\nAlert Breakdown:")
    print(f"  {'Cluster':<10} {'Frequency':<12} {'Risk':<10} {'Score':<8} {'Action':<15}")
    print("  " + "-" * 55)
    for a in alerts[:6]:
        act = "ESCALATE" if a["risk"] in ("CRITICAL", "HIGH") else "MONITOR" if a["risk"] == "MEDIUM" else "LOG_AND_MONITOR"
        print(f"  {a['cluster_id']:<10} {str(a['frequency']) + '%':<12} {a['risk']:<10} {a['risk_score']:<8} {act:<15}")

    print("\nEvaluation Metrics:")
    print(f"  - Precision         : {eval_res['metrics']['precision']:.4f}")
    print(f"  - Recall            : {eval_res['metrics']['recall']:.4f}")
    print(f"  - F1 Score          : {eval_res['metrics']['f1_score']:.4f}")
    print(f"  - False Pos Rate    : {eval_res['metrics']['false_positive_rate_pct']:.2f}%")
    print(f"  - Parsing Accuracy  : {eval_res['metrics']['parsing_accuracy']:.2f}%")
    print(f"  - Response Accuracy : {eval_res['metrics']['response_accuracy']:.2f}%")
    print(f"  - Chain Integrity   : {eval_res['metrics']['blockchain_integrity_pct']:.2f}%")
    print(f"  - Pipeline Latency  : {eval_res['performance']['total_pipeline_latency_ms']:.2f} ms")
    print("=" * 60 + "\n")

    return {
        "total_logs": total_logs,
        "templates": len(templates),
        "anomalies": len(alerts),
        "investigated": len(investigations),
        "responses": len(responses),
        "blockchain_blocks": total_blocks,
        "security_health_score": health_score,
        "risk_distribution": risk_counts,
        "evaluation_metrics": eval_res
    }


def main():
    parser = argparse.ArgumentParser(description="LogLens - AI-Assisted Multi-Agent Log Analysis Platform")
    parser.add_argument("--dataset", type=str, default="HDFS", choices=["HDFS", "Linux", "Apache"], help="Sample dataset to analyze")
    parser.add_argument("--file", type=str, default=None, help="Custom log file path to analyze")
    parser.add_argument("--serve", action="store_true", help="Start FastAPI REST API server on port 8000")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    args = parser.parse_args()

    if args.serve:
        import uvicorn
        print(f"Starting LogLens REST API server on http://127.0.0.1:{args.port}...")
        uvicorn.run("backend.main:app", host="127.0.0.1", port=args.port, reload=False)
    else:
        run_pipeline(dataset_name=args.dataset, log_file=args.file)


if __name__ == "__main__":
    main()
