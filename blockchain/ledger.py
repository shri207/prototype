import json
import os
from typing import Any, Dict, List, Union
from blockchain.chain import Block, LogEvidenceChain


def save_ledger(
    chain: Union[LogEvidenceChain, List[Union[Block, Dict[str, Any]]]],
    filename: str = "data/evidence_ledger.json"
) -> str:
    """
    Persists the structured evidence chain to a local readable JSON file.
    Does not store raw log files or datasets - stores only structured security
    evidence and integrity metadata.
    """
    if hasattr(chain, "get_chain"):
        blocks = chain.get_chain()
    else:
        blocks = chain

    serialized_chain = []
    for block in blocks:
        if hasattr(block, "to_dict"):
            serialized_chain.append(block.to_dict())
        elif isinstance(block, dict):
            serialized_chain.append(block)
        else:
            serialized_chain.append({
                "index": getattr(block, "index"),
                "timestamp": getattr(block, "timestamp"),
                "event": getattr(block, "event"),
                "previous_hash": getattr(block, "previous_hash"),
                "hash": getattr(block, "hash")
            })

    dirname = os.path.dirname(filename)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(serialized_chain, f, indent=2, ensure_ascii=False)

    try:
        from storage.database import get_db
        get_db().sync_blockchain_blocks(serialized_chain)
    except Exception:
        pass

    return filename



def load_ledger(filename: str = "data/evidence_ledger.json") -> LogEvidenceChain:
    """
    Loads the evidence chain from a local JSON file into a LogEvidenceChain instance.
    If the file does not exist, initializes and returns a fresh chain with a Genesis block.
    """
    if not os.path.exists(filename):
        return LogEvidenceChain()

    with open(filename, "r", encoding="utf-8") as f:
        raw_blocks = json.load(f)

    loaded_blocks = []
    for item in raw_blocks:
        block = Block(
            index=item["index"],
            timestamp=item["timestamp"],
            event=item["event"],
            previous_hash=item["previous_hash"],
            block_hash=item["hash"]
        )
        loaded_blocks.append(block)

    return LogEvidenceChain(blocks=loaded_blocks)
