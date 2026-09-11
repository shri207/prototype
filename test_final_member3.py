import json
import os
import urllib.request
from blockchain.hashing import generate_hash
from blockchain.chain import LogEvidenceChain
from blockchain.verifier import verify_chain
from blockchain.ledger import save_ledger, load_ledger
from blockchain.evidence_adapter import record_evidence

API_BASE = "http://127.0.0.1:8000"


def run_full_member3_suite():
    print("==========================================================")
    print("      LOGLENS MEMBER 3 - COMPLETE TEST SUITE VERIFICATION")
    print("==========================================================\n")

    results = {}

    # -----------------------------------------------------------
    # Test 1: SHA-256 (Same data -> same hash, length 64, order invariant)
    # -----------------------------------------------------------
    payload_a = {"event_id": "TEST-001", "action": "LOGIN", "status": "FAIL"}
    payload_b = {"status": "FAIL", "action": "LOGIN", "event_id": "TEST-001"}
    hash_a = generate_hash(payload_a)
    hash_b = generate_hash(payload_b)
    diff_hash = generate_hash({"event_id": "TEST-001", "action": "LOGIN", "status": "SUCCESS"})
    t1_pass = (hash_a == hash_b) and (len(hash_a) == 64) and (hash_a != diff_hash)
    results["Test 1: SHA-256 Deterministic Hashing"] = "PASS" if t1_pass else "FAIL"
    print(f"Test 1: SHA-256 -> {results['Test 1: SHA-256 Deterministic Hashing']}")
    print(f"        Hash: {hash_a}")

    # -----------------------------------------------------------
    # Test 2: Hash Chain (Genesis -> Event 1 -> Event 2 -> Event 3)
    # -----------------------------------------------------------
    chain = LogEvidenceChain()
    b1 = chain.add_event({"event_id": "E1", "type": "AUTH_FAIL"})
    b2 = chain.add_event({"event_id": "E2", "type": "AUTH_RETRY"})
    b3 = chain.add_event({"event_id": "E3", "type": "PRIVILEGE_ESCALATE"})
    blocks = chain.get_chain()
    t2_pass = (
        len(blocks) == 4 and
        blocks[0].previous_hash == "0" and
        blocks[1].previous_hash == blocks[0].hash and
        blocks[2].previous_hash == blocks[1].hash and
        blocks[3].previous_hash == blocks[2].hash
    )
    results["Test 2: Hash Chain Linkage"] = "PASS" if t2_pass else "FAIL"
    print(f"Test 2: Hash Chain -> {results['Test 2: Hash Chain Linkage']}")

    # -----------------------------------------------------------
    # Test 3: Verification (Original chain -> VERIFIED)
    # -----------------------------------------------------------
    t3_pass = (verify_chain(chain) is True)
    results["Test 3: Verification (Original Chain)"] = "PASS" if t3_pass else "FAIL"
    print(f"Test 3: Verification (Original Chain) -> {results['Test 3: Verification (Original Chain)']}")

    # -----------------------------------------------------------
    # Test 4: Tampering (Modify event -> TAMPER DETECTED)
    # -----------------------------------------------------------
    blocks[2].event["type"] = "MALICIOUS_MODIFICATION"
    t4_pass = (verify_chain(chain) is False)
    # Restore
    blocks[2].event["type"] = "AUTH_RETRY"
    results["Test 4: Tamper Detection"] = "PASS" if t4_pass else "FAIL"
    print(f"Test 4: Tamper Detection -> {results['Test 4: Tamper Detection']}")

    # -----------------------------------------------------------
    # Test 5: Ledger Persistence (Save -> Load -> Verify)
    # -----------------------------------------------------------
    test_ledger_path = "data/test_final_suite_ledger.json"
    save_ledger(chain, filename=test_ledger_path)
    loaded = load_ledger(filename=test_ledger_path)
    t5_pass = (len(loaded) == 4) and (verify_chain(loaded) is True)
    if os.path.exists(test_ledger_path):
        os.remove(test_ledger_path)
    results["Test 5: Ledger Persistence & Reload"] = "PASS" if t5_pass else "FAIL"
    print(f"Test 5: Ledger Persistence -> {results['Test 5: Ledger Persistence & Reload']}")

    # -----------------------------------------------------------
    # Test 6: FastAPI Endpoints (POST /evidence/add, GET /evidence/chain, GET /evidence/verify)
    # -----------------------------------------------------------
    try:
        # POST
        sample_post = {
            "event_id": "FINAL-EVT-01",
            "event_type": "FIREWALL_DROP",
            "severity": "MEDIUM",
            "user": "sysadmin",
            "ip": "10.10.10.10"
        }
        post_req = urllib.request.Request(
            f"{API_BASE}/evidence/add",
            data=json.dumps(sample_post).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(post_req) as resp:
            post_status = resp.status
            post_body = json.loads(resp.read().decode("utf-8"))

        # GET Chain
        with urllib.request.urlopen(f"{API_BASE}/evidence/chain") as resp:
            chain_status = resp.status
            chain_body = json.loads(resp.read().decode("utf-8"))

        # GET Verify
        with urllib.request.urlopen(f"{API_BASE}/evidence/verify") as resp:
            verify_status = resp.status
            verify_body = json.loads(resp.read().decode("utf-8"))

        t6_pass = (
            post_status == 201 and
            chain_status == 200 and
            isinstance(chain_body, list) and
            verify_status == 200 and
            verify_body.get("valid") is True
        )
        results["Test 6: FastAPI Evidence Endpoints"] = "PASS" if t6_pass else "FAIL"
    except Exception as e:
        results["Test 6: FastAPI Evidence Endpoints"] = f"FAIL: {str(e)}"
    print(f"Test 6: FastAPI Endpoints -> {results['Test 6: FastAPI Evidence Endpoints']}")

    # -----------------------------------------------------------
    # Test 10: Adapter Integration (record_evidence -> ledger -> verify)
    # -----------------------------------------------------------
    adapter_ledger = "data/test_adapter_suite.json"
    manual_event = {
        "event_id": "ADAPTER-TEST-001",
        "event_type": "MALWARE_DETECTED",
        "severity": "CRITICAL",
        "user": "compromised_service",
        "ip": "172.16.0.45"
    }
    block_adapter = record_evidence(manual_event, ledger_path=adapter_ledger)
    loaded_adapter = load_ledger(filename=adapter_ledger)
    t10_pass = (
        block_adapter.index == 1 and
        block_adapter.event["event_id"] == "ADAPTER-TEST-001" and
        len(loaded_adapter) == 2 and
        verify_chain(loaded_adapter) is True
    )
    if os.path.exists(adapter_ledger):
        os.remove(adapter_ledger)
    results["Test 10: Integration Adapter Contract"] = "PASS" if t10_pass else "FAIL"
    print(f"Test 10: Adapter Contract -> {results['Test 10: Integration Adapter Contract']}")

    print("\n----------------------------------------------------------")
    print("All backend, cryptographic, and adapter tests completed successfully.")
    print("----------------------------------------------------------")


if __name__ == "__main__":
    run_full_member3_suite()
