from blockchain.chain import LogEvidenceChain
from blockchain.verifier import verify_chain


def build_sample_chain():
    chain = LogEvidenceChain()
    chain.add_event({
        "event_id": "TEST-001",
        "event_type": "LOGIN_FAILED",
        "user": "test_user"
    })
    chain.add_event({
        "event_id": "TEST-002",
        "event_type": "LOGIN_SUCCESS",
        "user": "test_user"
    })
    return chain


def run_tests():
    print("=== TAMPER-EVIDENCE & CHAIN VERIFICATION TESTS ===\n")

    # TEST 1: Original chain
    chain1 = build_sample_chain()
    result1 = verify_chain(chain1)
    print(f"TEST 1 (Original chain) -> Result: {result1}, Expected: True")
    assert result1 is True, "TEST 1 Failed: Original chain should be verified as True"

    # TEST 2: Change event ("user": "test_user" -> "user": "attacker")
    chain2 = build_sample_chain()
    chain2.get_chain()[1].event["user"] = "attacker"
    result2 = verify_chain(chain2)
    print(f"TEST 2 (Tampered event payload) -> Result: {result2}, Expected: False")
    assert result2 is False, "TEST 2 Failed: Tampered event must fail verification"

    # TEST 3: Change previous_hash
    chain3 = build_sample_chain()
    chain3.get_chain()[1].previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    result3 = verify_chain(chain3)
    print(f"TEST 3 (Tampered previous_hash) -> Result: {result3}, Expected: False")
    assert result3 is False, "TEST 3 Failed: Tampered previous_hash must fail verification"

    # TEST 4: Change timestamp
    chain4 = build_sample_chain()
    chain4.get_chain()[1].timestamp += 500.0
    result4 = verify_chain(chain4)
    print(f"TEST 4 (Tampered timestamp) -> Result: {result4}, Expected: False")
    assert result4 is False, "TEST 4 Failed: Tampered timestamp must fail verification"

    # TEST 5: Change block hash
    chain5 = build_sample_chain()
    chain5.get_chain()[1].hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    result5 = verify_chain(chain5)
    print(f"TEST 5 (Tampered block hash) -> Result: {result5}, Expected: False")
    assert result5 is False, "TEST 5 Failed: Tampered block hash must fail verification"

    print("\nAll 5 verification tests PASSED successfully!")


if __name__ == "__main__":
    run_tests()
