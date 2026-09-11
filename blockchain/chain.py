import time
from typing import Any, Dict, List, Optional
from blockchain.hashing import generate_hash


class Block:
    """
    Represents an immutable block within the LogLens evidence hash chain.
    """
    def __init__(
        self,
        index: int,
        timestamp: float,
        event: Dict[str, Any],
        previous_hash: str,
        block_hash: Optional[str] = None
    ):
        self.index = index
        self.timestamp = timestamp
        self.event = event
        self.previous_hash = previous_hash
        self.hash = block_hash if block_hash is not None else self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Generates SHA-256 hash across index, timestamp, event, and previous_hash.
        """
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "event": self.event,
            "previous_hash": self.previous_hash
        }
        return generate_hash(block_data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event": self.event,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash='{self.hash[:10]}...', prev='{self.previous_hash[:10]}...')"


class LogEvidenceChain:
    """
    Manages the tamper-evident cryptographic hash chain for evidence logs.
    """
    def __init__(self, blocks: Optional[List[Block]] = None):
        self.chain: List[Block] = []
        if blocks is not None and len(blocks) > 0:
            self.chain = list(blocks)
        else:
            self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_event = {"type": "GENESIS"}
        genesis_block = Block(
            index=0,
            timestamp=0.0,
            event=genesis_event,
            previous_hash="0"
        )
        self.chain.append(genesis_block)

    def add_event(self, event: Dict[str, Any]) -> Block:
        """
        Appends a new event as a block linked to the latest block's hash.
        """
        previous_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            event=event,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        return new_block

    def get_chain(self) -> List[Block]:
        """
        Returns all blocks currently in the chain.
        """
        return self.chain

    def __len__(self) -> int:
        return len(self.chain)

    def __getitem__(self, item):
        return self.chain[item]

    def __iter__(self):
        return iter(self.chain)
