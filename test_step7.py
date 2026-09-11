import json
import os
import urllib.request

API_BASE = "http://127.0.0.1:8000"
LEDGER_PATH = "data/evidence_ledger.json"


def post_json(endpoint, data):
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def get_json(endpoint):
    req = urllib.request.Request(f"{API_BASE}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def run_test():
    print("=== STEP 7 THOROUGH API & TAMPER RESILIENCE TESTING ===\n")

    # Reset ledger to start completely fresh for this scenario
    if os.path.exists(LEDGER_PATH):
        os.remove(LEDGER_PATH)

    # 1. POST TEST-001
    evt1 = {
        "event_id": "TEST-001",
        "event_type": "LOGIN_FAILED",
        "severity": "HIGH",
        "user": "test_user",
        "ip": "10.0.0.5"
    }
    s1, r1 = post_json("/evidence/add", evt1)
    print(f"1. POST /evidence/add (TEST-001): Status {s1}")
    print(f"   Block Index: {r1['block']['index']}, Hash: {r1['block']['hash']}")
    assert s1 == 201

    # 2. POST TEST-002
    evt2 = {
        "event_id": "TEST-002",
        "event_type": "LOGIN_SUCCESS",
        "severity": "LOW",
        "user": "test_user",
        "ip": "10.0.0.5"
    }
    s2, r2 = post_json("/evidence/add", evt2)
    print(f"\n2. POST /evidence/add (TEST-002): Status {s2}")
    print(f"   Block Index: {r2['block']['index']}, Hash: {r2['block']['hash']}")
    assert s2 == 201

    # 3. POST TEST-003
    evt3 = {
        "event_id": "TEST-003",
        "event_type": "PRIVILEGE_ESCALATION",
        "severity": "CRITICAL",
        "user": "test_user",
        "ip": "10.0.0.5"
    }
    s3, r3 = post_json("/evidence/add", evt3)
    print(f"\n3. POST /evidence/add (TEST-003): Status {s3}")
    print(f"   Block Index: {r3['block']['index']}, Hash: {r3['block']['hash']}")
    assert s3 == 201

    # 4. GET /evidence/chain
    sc, chain = get_json("/evidence/chain")
    print(f"\n4. GET /evidence/chain: Status {sc}, Total blocks: {len(chain)}")
    for b in chain:
        print(f"   Block {b['index']}: Event={b['event'].get('event_type', b['event'].get('type'))}, Hash={b['hash'][:12]}..., PrevHash={b['previous_hash'][:12]}...")
    assert len(chain) == 4

    # 5. GET /evidence/verify (Original)
    sv1, rv1 = get_json("/evidence/verify")
    print(f"\n5. GET /evidence/verify (Original Chain): Status {sv1}, Result: {rv1}")
    assert rv1 == {"integrity": "VERIFIED", "valid": True}

    # 6. Simulate Tampering in data/evidence_ledger.json
    print("\n6. Simulating tampering in data/evidence_ledger.json...")
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        original_content = f.read()

    tampered_data = json.loads(original_content)
    # Tamper with Block 2 (TEST-002)'s user field
    original_user = tampered_data[2]["event"]["user"]
    tampered_data[2]["event"]["user"] = "attacker_imposter"

    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(tampered_data, f, indent=2)
    print(f"   Tampered Block 2 event 'user': '{original_user}' -> 'attacker_imposter'")

    # 7. GET /evidence/verify (Tampered)
    sv2, rv2 = get_json("/evidence/verify")
    print(f"\n7. GET /evidence/verify (Tampered Chain): Status {sv2}, Result: {rv2}")
    assert rv2 == {"integrity": "TAMPER_DETECTED", "valid": False}

    # 8. Restore original ledger
    print("\n8. Restoring original ledger...")
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        f.write(original_content)
    print("   Original ledger restored successfully.")

    # 9. GET /evidence/verify (Recovered)
    sv3, rv3 = get_json("/evidence/verify")
    print(f"\n9. GET /evidence/verify (Post-Recovery): Status {sv3}, Result: {rv3}")
    assert rv3 == {"integrity": "VERIFIED", "valid": True}

    print("\nAll Step 7 test scenarios PASSED with 100% precision!")


if __name__ == "__main__":
    run_test()
