import os
import unittest
from blockchain.evidence_adapter import record_evidence
from blockchain.ledger import load_ledger
from blockchain.verifier import verify_chain


class TestEvidenceAdapter(unittest.TestCase):
    def setUp(self):
        self.test_ledger_path = "data/test_adapter_ledger.json"
        if os.path.exists(self.test_ledger_path):
            os.remove(self.test_ledger_path)

    def tearDown(self):
        if os.path.exists(self.test_ledger_path):
            os.remove(self.test_ledger_path)

    def test_record_evidence_contract(self):
        # 1. Manually defined test event (e.g. simulating what Member 1 might pass)
        event_member1_sim = {
            "event_id": "EXT-001",
            "event_type": "LOGIN_FAILED",
            "severity": "HIGH",
            "user": "test_user",
            "ip": "10.0.0.5"
        }

        # 2. Pass through Evidence Adapter
        block1 = record_evidence(event_member1_sim, ledger_path=self.test_ledger_path)

        # 3. Verify Output Contract
        self.assertIsNotNone(block1)
        self.assertEqual(block1.index, 1, "First event block should have index 1")
        self.assertIsInstance(block1.timestamp, float)
        self.assertEqual(block1.event["event_id"], "EXT-001")
        self.assertEqual(len(block1.hash), 64, "Hash must be 64-char hex")
        self.assertTrue(hasattr(block1, "previous_hash"))

        # 4. Pass second manually defined event (e.g. simulating what Member 2 might pass)
        event_member2_sim = {
            "event_id": "ALERT-901",
            "event_type": "BRUTE_FORCE_CORRELATED",
            "severity": "CRITICAL",
            "source": "EXTERNAL_DETECTOR",
            "confidence": 0.98,
            "story": "Multiple failed attempts followed by privileged action"
        }

        block2 = record_evidence(event_member2_sim, ledger_path=self.test_ledger_path)

        # Verify second block linkage
        self.assertEqual(block2.index, 2)
        self.assertEqual(block2.previous_hash, block1.hash, "Block 2 must link to Block 1 hash")

        # 5. Verify Ledger Persistence and Cryptographic Chain Validity
        persisted_chain = load_ledger(filename=self.test_ledger_path)
        self.assertEqual(len(persisted_chain), 3, "Chain should have 3 blocks: Genesis + 2 events")
        self.assertTrue(verify_chain(persisted_chain), "Persisted chain must pass cryptographic verification")

    def test_invalid_input_type_handling(self):
        # Ensure adapter rejects non-dict input
        with self.assertRaises(TypeError):
            record_evidence("INVALID_STRING_INPUT", ledger_path=self.test_ledger_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
