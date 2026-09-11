import unittest
from blockchain.hashing import generate_hash


class TestCryptoHashing(unittest.TestCase):
    def setUp(self):
        self.sample_event = {
            "event_id": "TEST-001",
            "event_type": "LOGIN_FAILED",
            "severity": "HIGH",
            "user": "test_user"
        }

    def test_same_data_same_hash(self):
        hash1 = generate_hash(self.sample_event)
        hash2 = generate_hash(self.sample_event)
        self.assertEqual(hash1, hash2, "Identical data must yield the same hash")

    def test_different_data_different_hash(self):
        modified_event = dict(self.sample_event)
        modified_event["severity"] = "CRITICAL"
        hash1 = generate_hash(self.sample_event)
        hash2 = generate_hash(modified_event)
        self.assertNotEqual(hash1, hash2, "Modified data must yield a different hash")

    def test_hash_length(self):
        h = generate_hash(self.sample_event)
        self.assertEqual(len(h), 64, "SHA-256 hex string must be exactly 64 characters")
        self.assertTrue(all(c in "0123456789abcdef" for c in h), "Hash must be a valid hex string")

    def test_dict_key_order_invariance(self):
        # Dictionary with different insertion order of keys
        reordered_event = {
            "user": "test_user",
            "severity": "HIGH",
            "event_type": "LOGIN_FAILED",
            "event_id": "TEST-001"
        }
        hash1 = generate_hash(self.sample_event)
        hash2 = generate_hash(reordered_event)
        self.assertEqual(hash1, hash2, "Dictionary key ordering must not change the hash")


if __name__ == "__main__":
    unittest.main(verbosity=2)
