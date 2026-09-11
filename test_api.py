import os
from fastapi.testclient import TestClient
from backend.main import app


def test_api_endpoints():
    client = TestClient(app)

    print("=== TESTING FASTAPI MEMBER 3 ENDPOINTS ===\n")

    # 1. Test Root
    res_root = client.get("/")
    print(f"GET / -> Status: {res_root.status_code}, Response: {res_root.json()}")
    assert res_root.status_code == 200

    # 2. Test GET /evidence/chain
    res_chain = client.get("/evidence/chain")
    print(f"\nGET /evidence/chain -> Status: {res_chain.status_code}")
    chain_data = res_chain.json()
    print(f"Current blocks count: {len(chain_data)}")
    assert res_chain.status_code == 200
    assert len(chain_data) >= 1
    assert chain_data[0]["event"]["type"] == "GENESIS"

    # 3. Test POST /evidence/add
    sample_payload = {
        "event_id": "TEST-001",
        "event_type": "LOGIN_FAILED",
        "severity": "HIGH",
        "user": "test_user",
        "ip": "10.0.0.5"
    }
    res_add = client.post("/evidence/add", json=sample_payload)
    print(f"\nPOST /evidence/add -> Status: {res_add.status_code}")
    add_data = res_add.json()
    print(f"Added block index: {add_data['block']['index']}, Hash: {add_data['block']['hash']}")
    assert res_add.status_code == 201
    assert add_data["status"] == "SUCCESS"
    assert add_data["block"]["event"]["event_id"] == "TEST-001"

    # 4. Test GET /evidence/chain after addition
    res_chain2 = client.get("/evidence/chain")
    chain_data2 = res_chain2.json()
    print(f"\nGET /evidence/chain -> Status: {res_chain2.status_code}, New total blocks: {len(chain_data2)}")
    assert len(chain_data2) == len(chain_data) + 1

    # 5. Test GET /evidence/verify (Valid Chain)
    res_verify = client.get("/evidence/verify")
    print(f"\nGET /evidence/verify -> Status: {res_verify.status_code}, Body: {res_verify.json()}")
    verify_data = res_verify.json()
    assert res_verify.status_code == 200
    assert verify_data == {"integrity": "VERIFIED", "valid": True}

    print("\nAll FastAPI evidence endpoint tests PASSED!")


if __name__ == "__main__":
    test_api_endpoints()
