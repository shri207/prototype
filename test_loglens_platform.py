import json
import os
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from parser.source_detector import detect_log_source
from parser.loader import load_log_records, LogFormatError
from parser.preprocessor import analyze_log_line, classify_token
from parser.template_miner import mine_templates
from detector.scoring_engine import calculate_frequency_score, evaluate_cluster_risk, map_score_to_risk
from detector.anomaly_detector import detect_cluster_anomalies
from detector.alert_engine import AlertEngine
from agents.investigator_agent import InvestigatorAgent
from agents.response_agent import ResponseAgent
from agents.agent_manager import AgentManager
from blockchain.chain import Block, LogEvidenceChain
from blockchain.hashing import generate_hash
from blockchain.verifier import verify_chain
from blockchain.evidence_adapter import record_evidence
from blockchain.ledger import load_ledger, save_ledger
from storage.database import Database
from evaluation.evaluator import evaluate_system_performance


class TestLogLensPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = "data/test_platform.db"
        cls.test_ledger_path = "data/test_platform_ledger.json"
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        if os.path.exists(cls.test_ledger_path):
            os.remove(cls.test_ledger_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        if os.path.exists(cls.test_ledger_path):
            os.remove(cls.test_ledger_path)

    def test_01_source_detection(self):
        hdfs_path = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
        linux_path = PROJECT_ROOT / "data" / "loghub" / "Linux" / "Linux_2k.log"
        apache_path = PROJECT_ROOT / "data" / "loghub" / "Apache" / "Apache_2k.log"

        self.assertEqual(detect_log_source(hdfs_path), "HDFS")
        self.assertEqual(detect_log_source(linux_path), "Linux")
        self.assertEqual(detect_log_source(apache_path), "Apache")

    def test_02_log_loader_and_preprocessing(self):
        hdfs_path = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
        records = load_log_records(hdfs_path)
        self.assertEqual(len(records), 2000)
        self.assertEqual(records[0]["line_id"], 1)
        self.assertIn("raw_log", records[0])
        self.assertEqual(records[0]["source"], "HDFS")

        # Test token classifier
        self.assertEqual(classify_token("192.168.1.1"), "IP")
        self.assertEqual(classify_token("blk_12345"), "BLOCK_ID")
        self.assertEqual(classify_token("GET"), "HTTP_METHOD")

    def test_03_template_mining(self):
        hdfs_path = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
        records = load_log_records(hdfs_path)
        templates = mine_templates(records)
        self.assertEqual(len(templates), 16)
        cluster_ids = [t["cluster_id"] for t in templates]
        self.assertIn("C001", cluster_ids)

    def test_04_scoring_engine(self):
        self.assertEqual(map_score_to_risk(85), "CRITICAL")
        self.assertEqual(map_score_to_risk(70), "HIGH")
        self.assertEqual(map_score_to_risk(45), "MEDIUM")
        self.assertEqual(map_score_to_risk(15), "LOW")

        cluster = {
            "cluster_id": "C011",
            "template": "Starting thread to transfer block blk_<*> to <*>:<*>",
            "frequency": 0.05,
            "count": 1,
            "signature": "WORD NUMBER BLOCK_ID IP"
        }
        res = evaluate_cluster_risk(cluster, raw_samples=["081110 211541 18 INFO dfs.DataNode: Starting thread"])
        self.assertGreaterEqual(res["risk_score"], 60)
        self.assertIn(res["risk"], ("HIGH", "CRITICAL"))

    def test_05_anomaly_detection_and_alerts(self):
        hdfs_path = PROJECT_ROOT / "data" / "loghub" / "HDFS" / "HDFS_2k.log"
        records = load_log_records(hdfs_path)
        templates = mine_templates(records)
        anomalies = detect_cluster_anomalies(templates, records, alert_threshold=30)
        self.assertGreater(len(anomalies), 0)

        alert_engine = AlertEngine(alert_threshold=30)
        alerts = alert_engine.generate_alerts(anomalies, records, source="HDFS")
        self.assertGreater(len(alerts), 0)
        self.assertTrue(alerts[0]["alert_id"].startswith("ALT-"))
        self.assertIn("breakdown", alerts[0])
        self.assertIn("evidence", alerts[0])

    def test_06_multi_agent_lifecycle(self):
        alert = {
            "alert_id": "ALT-001",
            "cluster_id": "C011",
            "source": "HDFS",
            "template": "Starting thread to transfer block blk_<*>",
            "risk": "HIGH",
            "risk_score": 82,
            "confidence": 0.91,
            "count": 1,
            "frequency": 0.05,
            "evidence": [{"line_id": 912, "raw_log": "Sample log line", "timestamp": "081110 211541"}],
            "affected_lines": [912],
            "reason": "Rare high-severity event detected."
        }

        inv_agent = InvestigatorAgent()
        investigation = inv_agent.investigate(alert)
        self.assertEqual(investigation["status"], "INVESTIGATED")
        self.assertEqual(investigation["recommended_action"], "ESCALATE")

        resp_agent = ResponseAgent()
        response = resp_agent.formulate_response(investigation)
        self.assertEqual(response["action"], "ESCALATE")
        self.assertIn(response["priority"], ("CRITICAL", "HIGH"))


        # Test Agent Manager orchestration with custom test ledger
        agent_mgr = AgentManager(investigator=inv_agent, responder=resp_agent)
        res = agent_mgr.process_alerts([alert], record_to_blockchain=True, ledger_path=self.test_ledger_path)
        self.assertEqual(len(res["investigations"]), 1)
        self.assertEqual(len(res["responses"]), 1)
        self.assertEqual(len(res["blockchain_records"]), 1)

    def test_07_blockchain_and_tamper_detection(self):
        chain = load_ledger(filename=self.test_ledger_path)
        self.assertTrue(verify_chain(chain))

        # Tamper test: modify event payload in block 1
        blocks = chain.get_chain()
        self.assertGreaterEqual(len(blocks), 2)
        tampered_event = dict(blocks[1].event)
        tampered_event["severity"] = "TAMPERED_LEVEL"
        blocks[1].event = tampered_event

        # Verification must detect the tampering
        self.assertFalse(verify_chain(chain))

    def test_08_sqlite_persistence(self):
        db = Database(db_path=self.test_db_path)
        db.save_analysis_run(
            logs=[{"line_id": 1, "raw_log": "Test line 1", "source": "HDFS", "timestamp": "081109 203615", "cluster_id": "C001"}],
            templates=[{"cluster_id": "C001", "template": "Test <*> pattern", "count": 1, "frequency": 100.0, "signature": "WORD"}],
            alerts=[{"alert_id": "ALT-001", "cluster_id": "C001", "source": "HDFS", "risk": "LOW", "risk_score": 20, "confidence": 0.8, "template": "Test", "reason": "Test reason", "breakdown": {}, "evidence": []}],
            investigations=[{"agent_id": "INV-001", "alert_id": "ALT-001", "cluster_id": "C001", "risk": "LOW", "risk_score": 20, "confidence": 0.8, "status": "INVESTIGATED", "reason": "Test", "recommended_action": "LOG_AND_MONITOR"}],
            responses=[{"response_id": "RESP-001", "alert_id": "ALT-001", "cluster_id": "C001", "action": "LOG_AND_MONITOR", "priority": "LOW", "agent_id": "RESP-001", "reason": "Test", "risk_score": 20}]
        )

        logs, total = db.get_logs()
        self.assertEqual(total, 1)
        self.assertEqual(len(db.get_templates()), 1)
        self.assertEqual(len(db.get_alerts()), 1)
        self.assertEqual(len(db.get_investigations()), 1)
        self.assertEqual(len(db.get_responses()), 1)

    def test_09_evaluation_benchmarks(self):
        res = evaluate_system_performance(dataset_name="HDFS")
        self.assertEqual(res["total_logs"], 2000)
        self.assertEqual(res["metrics"]["parsing_accuracy"], 100.0)
        self.assertGreater(res["metrics"]["precision"], 0.0)
        self.assertGreater(res["metrics"]["recall"], 0.0)
        self.assertEqual(res["metrics"]["blockchain_integrity_pct"], 100.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
