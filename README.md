# LogLens — Cybersecurity Evidence Subsystem (Member 3)

LogLens is a collaborative cybersecurity final-year project designed for automated log ingestion, multi-agent threat correlation, and tamper-evident security evidence management.

This subsystem (**Member 3**) is responsible for:
- **Evidence Integrity**: Deterministic SHA-256 cryptographic hashing of security events.
- **Tamper-Evident Hash Chain**: Sequential cryptographic linking of evidence blocks.
- **Local Evidence Ledger**: Persistent, readable JSON storage (`data/evidence_ledger.json`).
- **Integrity Verification**: Audit engine detecting any historical tampering or modifications.
- **FastAPI Endpoints**: REST API for evidence ingestion, ledger retrieval, and verification.
- **Evidence Dashboard**: React/Vite/Tailwind SOC interface for monitoring and auditing.
- **Integration Interfaces**: Decoupled ingestion entry points for Member 1 and Member 2.

---

## Integration Specification & Teammate Guide

The Member 3 evidence layer does **not** assume or require specific upstream logic. It accepts structured Python dictionaries and immediately commits them into the cryptographic hash chain.

### How Member 1 can send structured events to Member 3

When **Member 1 (Log Ingestion & Parsing)** extracts and parses a log entry into a structured dictionary, pass it directly to `record_evidence(event)`.

#### Expected Member 1 Schema
```python
{
    "event_id": "M1-EVT-1001",           # Unique string ID
    "event_type": "SSH_AUTH_FAIL",        # Event classification / category
    "timestamp": "2026-09-11T12:00:00Z",  # Event timestamp
    "severity": "HIGH",                  # CRITICAL | HIGH | MEDIUM | LOW | INFO
    "user": "ubuntu",                    # Target user account
    "ip": "192.168.1.105"                # Source IP address
}
```

#### Python Integration (Member 1)
```python
from blockchain.evidence_adapter import record_evidence

# 1. Member 1 parses raw log into structured dictionary
parsed_event = {
    "event_id": "M1-EVT-1001",
    "event_type": "SSH_AUTH_FAIL",
    "timestamp": "2026-09-11T12:00:00Z",
    "severity": "HIGH",
    "user": "ubuntu",
    "ip": "192.168.1.105"
}

# 2. Record directly into Member 3 evidence hash chain
committed_block = record_evidence(parsed_event)
print(f"Secured in Block #{committed_block.index} with Hash: {committed_block.hash}")
```

#### HTTP API Alternative (Member 1)
```bash
curl -X POST "http://127.0.0.1:8000/evidence/add" \
     -H "Content-Type: application/json" \
     -d '{
       "event_id": "M1-EVT-1001",
       "event_type": "SSH_AUTH_FAIL",
       "severity": "HIGH",
       "user": "ubuntu",
       "ip": "192.168.1.105"
     }'
```

---

### How Member 2 can send alerts to Member 3

When **Member 2 (Multi-Agent Detection & Alert Correlation)** generates an alert or correlated attack story, pass the alert dictionary directly to `record_evidence(alert)`.

#### Expected Member 2 Alert Schema
```python
{
    "alert_id": "M2-ALT-9001",                          # Unique alert identifier
    "alert_type": "SUSPICIOUS_BRUTE_FORCE",             # Alert classification
    "severity": "CRITICAL",                             # Alert severity level
    "user": "admin",                                    # Target or compromised account
    "source_ip": "203.0.113.42",                        # Attacking or anomalous IP
    "description": "Correlated 15 failed logins followed by privilege escalation attempt"
}
```

#### Python Integration (Member 2)
```python
from blockchain.evidence_adapter import record_evidence

# 1. Member 2 multi-agent engine outputs correlated alert
alert = {
    "alert_id": "M2-ALT-9001",
    "alert_type": "SUSPICIOUS_BRUTE_FORCE",
    "severity": "CRITICAL",
    "user": "admin",
    "source_ip": "203.0.113.42",
    "description": "Correlated 15 failed logins followed by privilege escalation attempt"
}

# 2. Record directly into Member 3 evidence hash chain
committed_block = record_evidence(alert)
print(f"Secured in Block #{committed_block.index} with Hash: {committed_block.hash}")
```

#### HTTP API Alternative (Member 2)
```bash
curl -X POST "http://127.0.0.1:8000/evidence/add" \
     -H "Content-Type: application/json" \
     -d '{
       "event_id": "M2-ALT-9001",
       "event_type": "SUSPICIOUS_BRUTE_FORCE",
       "severity": "CRITICAL",
       "user": "admin",
       "ip": "203.0.113.42",
       "description": "Correlated 15 failed logins followed by privilege escalation attempt"
     }'
```

---

## Output Contract (Return Value)

When calling `record_evidence(data)`, Member 3 returns a `Block` object containing:

| Field | Type | Description |
| :--- | :--- | :--- |
| `index` | `int` | Sequential height in the cryptographic chain (Genesis = 0) |
| `timestamp` | `float` | POSIX epoch timestamp when evidence was committed |
| `event` | `dict` | Original structured evidence payload preserved intact |
| `previous_hash` | `str` | 64-character SHA-256 hash of parent block |
| `hash` | `str` | 64-character SHA-256 hash calculated over this block's data |

Can also be converted to a dictionary via `committed_block.to_dict()`.

---

## Running the Services

### 1. Start Member 3 Backend API
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- API Docs (Swagger UI): `http://127.0.0.1:8000/docs`

### 2. Start Member 3 SOC Dashboard
```powershell
cd frontend
npm run dev
```
- Web Dashboard: `http://localhost:5173`

---

## Running Member 3 Test Suites
```powershell
python test_crypto.py             # SHA-256 deterministic hashing tests
python test_chain.py              # Cryptographic block linkage tests
python test_verifier.py           # 5-stage tamper detection tests
python test_ledger.py             # Local JSON ledger persistence tests
python test_api.py                # FastAPI endpoints test
python test_adapter.py            # Evidence adapter integration contract tests
python test_integration_specs.py  # Member 1 & Member 2 schema ingestion tests
```
