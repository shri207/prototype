import json
from blockchain.chain import LogEvidenceChain


def test_chain():
    # Initialize evidence chain
    chain = LogEvidenceChain()

    event1 = {
        "event_id": "TEST-001",
        "event_type": "LOGIN_FAILED"
    }

    event2 = {
        "event_id": "TEST-002",
        "event_type": "LOGIN_SUCCESS"
    }

    event3 = {
        "event_id": "TEST-003",
        "event_type": "PRIVILEGE_ESCALATION"
    }

    # Add events to chain
    chain.add_event(event1)
    chain.add_event(event2)
    chain.add_event(event3)

    blocks = chain.get_chain()

    # Print chain
    print("=== LOGLENS EVIDENCE CHAIN ===")
    for block in blocks:
        print(f"\nBlock Index   : {block.index}")
        print(f"Timestamp     : {block.timestamp}")
        print(f"Event         : {json.dumps(block.event)}")
        print(f"Previous Hash : {block.previous_hash}")
        print(f"Current Hash  : {block.hash}")

    print("\n=== VERIFYING PREVIOUS HASH LINKAGE ===")

    # Block 1 previous_hash == Genesis hash
    assert blocks[1].previous_hash == blocks[0].hash, "Verification Failed: Block 1 previous_hash != Genesis hash"
    print("PASS: Block 1 previous_hash == Genesis hash")

    # Block 2 previous_hash == Block 1 hash
    assert blocks[2].previous_hash == blocks[1].hash, "Verification Failed: Block 2 previous_hash != Block 1 hash"
    print("PASS: Block 2 previous_hash == Block 1 hash")

    # Block 3 previous_hash == Block 2 hash
    assert blocks[3].previous_hash == blocks[2].hash, "Verification Failed: Block 3 previous_hash != Block 2 hash"
    print("PASS: Block 3 previous_hash == Block 2 hash")

    print("\nAll hash chain linkage checks PASSED successfully.")


if __name__ == "__main__":
    test_chain()
