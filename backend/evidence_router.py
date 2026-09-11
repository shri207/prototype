from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict

from blockchain.evidence_adapter import record_evidence
from blockchain.ledger import load_ledger
from blockchain.verifier import verify_chain

evidence_router = APIRouter(prefix="/evidence", tags=["Member 3 - Evidence Integrity"])


class EvidenceEventRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    event_type: str
    severity: Optional[str] = "MEDIUM"
    user: Optional[str] = None
    ip: Optional[str] = None


@evidence_router.post("/add", status_code=status.HTTP_201_CREATED)
def add_evidence_event(payload: EvidenceEventRequest):
    """
    Ingests structured security evidence into the tamper-evident hash chain
    and persists the updated chain into the local ledger via the Member 3 adapter.
    """
    try:
        new_block = record_evidence(payload.model_dump())
        return {
            "status": "SUCCESS",
            "message": f"Evidence block #{new_block.index} recorded into hash chain.",
            "block": new_block.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record evidence block: {str(e)}"
        )


@evidence_router.get("/chain", response_model=List[Dict[str, Any]])
def get_evidence_chain():
    """
    Returns the full chronological tamper-evident evidence chain from the ledger.
    """
    chain = load_ledger()
    return [block.to_dict() for block in chain.get_chain()]


@evidence_router.get("/verify")
def verify_evidence_integrity():
    """
    Loads the evidence ledger and verifies the complete cryptographic hash chain.
    Returns VERIFIED if all block hashes and linkages are intact, or TAMPER_DETECTED otherwise.
    """
    chain = load_ledger()
    is_valid = verify_chain(chain)

    if is_valid:
        return {
            "integrity": "VERIFIED",
            "valid": True
        }
    else:
        return {
            "integrity": "TAMPER_DETECTED",
            "valid": False
        }
