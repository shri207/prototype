import hashlib
import json


def generate_hash(data):
    """
    Generates a deterministic SHA-256 hexadecimal hash for evidence integrity.
    Supports dictionaries (converted via deterministic JSON with sorted keys and compact separators)
    as well as strings.
    """
    if isinstance(data, dict):
        data = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()
