import os
import unittest
from blockchain.evidence_adapter import record_evidence
from blockchain.ledger import load_ledger
from blockchain.verifier import verify_chain


class TestIntegrationSpecs(unittest.TestCase):
    def setUp(self):
        self.test_ledger = "data/test_specs_ledger.json"
        if os.path.exists(self.test_ledger):
            os.remove(self.test_ledger)

    def tearDown(self):
        if os.path.exists(self.test_ledger):
            os.remove(self.test_ledger)

    def test_member_1_schema_ingestion(self):
        # Manually defined dictionary simulating Member 1 parser output
        m1_event = {
            "event_id": "M1-EVT-001",
            "event_type": "SSH_AUTH_FAIL",
            "timestamp": "2026-09-11T12:00:00Z",
            "severity": "HIGH",
            "user": "ubuntu",
            "ip": "192.168.1.105"
        }
        block = record_evidence(m1_event, ledger_path=self.test_ledger)
        self.assertEqual(block.index, 1)
        self.assertEqual(block.event["event_id"], "M1-EVT-001")
        self.assertEqual(block.event["event_type"], "SSH_AUTH_FAIL")
        self.assertEqual(len(block.hash), 64)

    def test_member_2_schema_ingestion(self):
        # Manually defined dictionary simulating Member 2 alert output
        m2_alert = {
            "alert_id": "M2-ALT-901",
            "alert_type": "SUSPICIOUS_BRUTE_FORCE",
            "severity": "CRITICAL",
            "user": "admin",
            "source_ip": "203.0.113.42",
            "description": "Correlated 15 failed logins followed by privilege escalation attempt"
        }
        block = record_evidence(m2_alert, ledger_path=self.test_ledger)
        self.assertEqual(block.index, 1)
        self.assertEqual(block.event["alert_id"], "M2-ALT-901")
        self.assertEqual(block.event["alert_type"], "SUSPICIOUS_BRUTE_FORCE")
        self.assertEqual(len(block.hash), 64)

    def test_mixed_pipeline_verification(self):
        # Verify seamless chaining of Member 1 event followed by Member 2 alert
        m1_event = {
            "event_id": "M1-EVT-002",
            "event_type": "FILE_INTEGRITY_CHANGE",
            "timestamp": "2026-09-11T12:05:00Z",
            "severity": "MEDIUM",
            "user": "daemon",
            "ip": "127.0.0.1"
        }
        m2_alert = {
            "alert_id": "M2-ALT-902",
            "alert_type": "ATTACK_STORY_FORMED",
            "severity": "HIGH",
            "user": "daemon",
            "source_ip": "127.0.0.1",
            "description": "Multi-agent consensus confirms automated tampering attempt"
        }

        b1 = record_evidence(m1_event, ledger_path=self.test_ledger)
        b2 = record_evidence(m2_alert, ledger_path=self.test_ledger)

        # Confirm cryptographic link
        self.assertEqual(b2.previous_hash, b1.hash)

        # Confirm full ledger verification
        chain = load_ledger(filename=self.test_ledger)
        self.assertEqual(len(chain), 3)  # Genesis + Block 1 + Block 2
        self.assertTrue(verify_chain(chain))


if __name__ == "__main__":
    unittest.main(verbosity=2)
