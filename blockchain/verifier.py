"""
LogLens - Tamper Evidence & Detection Verifier (Member 3)

NOTE: This system provides cryptographic tamper EVIDENCE and DETECTION.
It detects any unauthorized modification, tampering, or reordering of historical evidence.
It does not prevent physical modification of local storage files; rather, any tampering
immediately breaks the hash chain and is reliably detected upon verification.
"""

from typing import Any, Dict, List, Union
from blockchain.hashing import generate_hash
from blockchain.chain import Block, LogEvidenceChain


def verify_chain(chain: Union[LogEvidenceChain, List[Union[Block, Dict[str, Any]]]]) -> bool:
    """
    Verifies the cryptographic integrity of the evidence hash chain.

    Checks:
    1. previous_hash linkage between adjacent blocks
    2. block hash correctness (recalculating the SHA-256 hash)
    3. event integrity
    4. timestamp integrity
    5. previous_hash integrity

    Returns True if the chain is valid and untampered; False otherwise.
    """
    if hasattr(chain, "get_chain"):
        blocks = chain.get_chain()
    else:
        blocks = chain

    if not blocks:
        return False

    for i, block in enumerate(blocks):
        # Support both Block objects and dictionary records
        if isinstance(block, Block):
            index = block.index
            timestamp = block.timestamp
            event = block.event
            prev_hash = block.previous_hash
            current_hash = block.hash
        elif isinstance(block, dict):
            index = block.get("index")
            timestamp = block.get("timestamp")
            event = block.get("event")
            prev_hash = block.get("previous_hash")
            current_hash = block.get("hash")
        else:
            return False

        # 1. Verify index sequence
        if index != i:
            return False

        # 2. Verify previous_hash linkage
        if i == 0:
            if prev_hash != "0":
                return False
        else:
            prev_block = blocks[i - 1]
            prev_block_hash = prev_block.hash if isinstance(prev_block, Block) else prev_block.get("hash")
            if prev_hash != prev_block_hash:
                return False

        # 3. Verify block hash correctness (covers event, timestamp, index, and previous_hash integrity)
        block_data = {
            "index": index,
            "timestamp": timestamp,
            "event": event,
            "previous_hash": prev_hash
        }
        recalculated_hash = generate_hash(block_data)
        if recalculated_hash != current_hash:
            return False

    return True
