"""
LogLens - Integration Adapter for Member 3 Evidence Subsystem

INTERFACE CONTRACT FOR TEAM COLLABORATION:
------------------------------------------
This adapter serves as the entry point for other subsystems to record evidence
without needing to know internal blockchain, cryptographic hashing, or file persistence mechanics.

INPUT CONTRACT:
- Type: Python dictionary (dict)
- Content: Structured security event or alert metadata.
  Expected / common fields:
    - event_id (str): Unique identifier for the event or alert
    - event_type (str): Category/type of event (e.g., 'LOGIN_FAILED', 'SQL_INJECTION', 'ATTACK_STORY')
    - severity (str, optional): 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
    - user (str, optional): Associated user account
    - ip (str, optional): Associated IP address
    - Any additional structured fields produced by Member 1 or Member 2 are preserved.

OUTPUT CONTRACT:
- Type: Block (also serializable to dict via .to_dict())
- Fields:
    - index (int): Sequential block number in the cryptographic chain
    - timestamp (float): POSIX timestamp when the evidence was secured
    - event (dict): The original structured evidence payload
    - previous_hash (str): SHA-256 hash of the preceding block
    - hash (str): 64-character SHA-256 hexadecimal digest of this block
"""

from typing import Any, Dict
from blockchain.chain import Block
from blockchain.ledger import load_ledger, save_ledger


def record_evidence(
    event: Dict[str, Any],
    ledger_path: str = "data/evidence_ledger.json"
) -> Block:
    """
    Accepts a structured security event (from Member 1, Member 2, or manual source),
    appends it to the cryptographic hash chain, and persists it to the evidence ledger.

    :param event: Normal Python dictionary containing structured event data.
    :param ledger_path: Filepath where the evidence ledger is stored.
    :return: The newly created Block object conforming to the output contract.
    """
    if not isinstance(event, dict):
        raise TypeError(f"Expected event to be a Python dict, received {type(event).__name__}")

    # 1. Load current chain state from ledger
    chain = load_ledger(filename=ledger_path)

    # 2. Append structured event to hash chain
    new_block = chain.add_event(event)

    # 3. Persist updated chain to ledger storage
    save_ledger(chain, filename=ledger_path)

    return new_block
