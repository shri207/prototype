import os
from blockchain.chain import LogEvidenceChain
from blockchain.ledger import save_ledger, load_ledger
from blockchain.verifier import verify_chain


def run_test():
    test_ledger_path = "data/test_evidence_ledger.json"

    # Clean up prior test artifact if exists
    if os.path.exists(test_ledger_path):
        os.remove(test_ledger_path)

    # 1. Create chain
    chain = LogEvidenceChain()

    # 2. Add 3 independent local events
    event1 = {
        "event_id": "SEC-EVT-101",
        "action": "PORT_SCAN_DETECTED",
        "source_ip": "192.168.1.50"
    }
    event2 = {
        "event_id": "SEC-EVT-102",
        "action": "AUTH_BRUTE_FORCE",
        "target_user": "admin"
    }
    event3 = {
        "event_id": "SEC-EVT-103",
        "action": "ACCOUNT_LOCKED",
        "target_user": "admin"
    }

    chain.add_event(event1)
    chain.add_event(event2)
    chain.add_event(event3)

    # 3. Save ledger
    saved_path = save_ledger(chain, filename=test_ledger_path)
    assert os.path.exists(saved_path), "Ledger file was not created"
    print("Ledger saved.")

    # 4. Load ledger
    loaded_chain = load_ledger(filename=test_ledger_path)
    assert len(loaded_chain) == 4, f"Expected 4 blocks (1 Genesis + 3 events), got {len(loaded_chain)}"
    print("Ledger loaded.")

    # 5. Verify loaded chain
    is_valid = verify_chain(loaded_chain)
    assert is_valid is True, "Verification failed for loaded ledger"
    print("Integrity valid.")

    # Clean up test ledger file
    if os.path.exists(test_ledger_path):
        os.remove(test_ledger_path)


if __name__ == "__main__":
    run_test()
