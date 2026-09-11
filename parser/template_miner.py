from collections import defaultdict
from pathlib import Path
import re
from typing import Any, Dict, List, Union

try:
    from .loader import load_log_file
    from .signature import generate_signature
except ImportError:
    from loader import load_log_file
    from signature import generate_signature


VARIABLE = "<*>"


# ==========================================
# EXTRACT LOG CONTENT
# ==========================================

def extract_log_content(log_line: str) -> str:
    """
    Extract the actual message/content part from a raw log line.
    Preserves exact behavior for HDFS, Linux, Apache, and generic logs.
    """
    parts = log_line.split()
    if not parts:
        return ""

    # HDFS format: Date Time PID LEVEL Component: Content
    if (
        len(parts) >= 6
        and parts[3] in {"INFO", "WARN", "ERROR", "DEBUG", "FATAL"}
    ):
        component_end = 4
        for i in range(4, min(len(parts), 10)):
            if parts[i].endswith(":"):
                component_end = i
                break
        return " ".join(parts[component_end + 1:])

    # Linux style: Month Day Time Host Process[PID]: Content
    if len(parts) >= 5:
        for i in range(3, min(len(parts), 8)):
            if ":" in parts[i]:
                prefix = parts[i]
                if prefix.endswith(":"):
                    return " ".join(parts[i + 1:])

    # Apache style: [Date] [Level] Content
    if len(parts) >= 3 and parts[0].startswith("["):
        bracket_count = 0
        for i, token in enumerate(parts):
            bracket_count += token.count("[")
            if bracket_count >= 2:
                return " ".join(parts[i + 1:])

    # Fallback
    return log_line.strip()


# ==========================================
# NORMALIZE CONTENT
# ==========================================

def normalize_content(content: str) -> str:
    """
    Normalize variable values while preserving
    the structural format expected by LogHub.
    """
    # HDFS block IDs: blk_12345 or blk_-12345 -> blk_<*>
    content = re.sub(r"blk_-?\d+", "blk_<*>", content)

    # IP:PORT followed by colon: 10.251.30.85:50010:Got -> <*>:<*>:Got
    content = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}:\d+:", "<*>:<*>:", content)

    # Normal IP:PORT: 10.251.30.85:50010 -> <*>:<*>
    content = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}:\d+\b", "<*>:<*>", content)

    # /IP:PORT -> /<*>:<*>
    content = re.sub(r"/\d{1,3}(?:\.\d{1,3}){3}:\d+", "/<*>:<*>", content)

    # /IP -> /<*>
    content = re.sub(r"/\d{1,3}(?:\.\d{1,3}){3}", "/<*>", content)

    # HDFS delete path
    content = re.sub(r"/mnt/.*/(blk_<\*>)", r"/<*>/\1", content)

    # HDFS temporary path
    content = re.sub(r"/user/.*/part-\d+\.", "/<*>/part-<*>.", content)

    # Normalize pure integers to variable wildcard
    tokens = content.split()
    result = []
    for token in tokens:
        if re.fullmatch(r"-?\d+", token):
            result.append(VARIABLE)
        else:
            result.append(token)

    return " ".join(result)


# ==========================================
# BUILD CLUSTERS
# ==========================================

def build_clusters(logs: List[Union[str, Dict[str, Any]]]):
    """
    Group log lines using their structural signatures.
    Handles both raw strings and structured record dictionaries.
    """
    clusters = defaultdict(list)
    line_mappings = defaultdict(list)

    for idx, item in enumerate(logs, start=1):
        if isinstance(item, dict):
            raw_line = item.get("raw_log", "")
            line_id = item.get("line_id", idx)
        else:
            raw_line = str(item)
            line_id = idx

        content = extract_log_content(raw_line)
        normalized_content = normalize_content(content)
        signature = generate_signature(normalized_content)

        clusters[signature].append(normalized_content)
        line_mappings[signature].append(line_id)

    return clusters, line_mappings


# ==========================================
# MINE ONE TEMPLATE
# ==========================================

def mine_template(log_lines: List[str]) -> str:
    """
    Compare tokens position-by-position and generate a common template.
    """
    tokenized_logs = [log.split() for log in log_lines]
    if not tokenized_logs:
        return ""

    first_log = tokenized_logs[0]

    # HDFS special case: BLOCK* ask <ip>:<port> to delete blk_* ...
    if (
        len(first_log) >= 5
        and first_log[0] == "BLOCK*"
        and first_log[1] == "ask"
        and "to" in first_log
        and "delete" in first_log
    ):
        delete_index = first_log.index("delete")
        prefix = first_log[:delete_index + 1]
        if delete_index + 1 < len(first_log):
            prefix.append("blk_<*>")
        return " ".join(prefix)

    # Normal template alignment
    max_length = max(len(tokens) for tokens in tokenized_logs)
    template = []

    for position in range(max_length):
        values = []
        for tokens in tokenized_logs:
            if position < len(tokens):
                values.append(tokens[position])

        unique_values = set(values)
        if len(unique_values) == 1:
            template.append(values[0])
        else:
            template.append(VARIABLE)

    return " ".join(template)


# ==========================================
# MINE TEMPLATES
# ==========================================

def mine_templates(logs: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Build clusters and mine one template per cluster.
    Provides cluster_id, template, count, frequency, and sample line IDs.
    """
    total_logs = len(logs) if logs else 1
    clusters, line_mappings = build_clusters(logs)
    templates = []

    for cluster_idx, (signature, cluster_logs) in enumerate(clusters.items(), start=1):
        template = mine_template(cluster_logs)
        size = len(cluster_logs)
        frequency = round((size / total_logs) * 100, 3)

        templates.append({
            "cluster_id": f"C{cluster_idx:03d}",
            "signature": signature,
            "size": size,
            "count": size,
            "frequency": frequency,
            "template": template,
            "sample_lines": line_mappings[signature][:10],
            "total_lines": line_mappings[signature]
        })

    return templates


if __name__ == "__main__":
    log_file = Path("data/loghub/HDFS/HDFS_2k.log")
    logs = load_log_file(log_file)
    templates = mine_templates(logs)

    print("================================")
    print("     LogLens Template Miner")
    print("================================")
    print(f"File: {log_file}")
    print(f"Total logs: {len(logs)}")
    print(f"Clusters: {len(templates)}")
    print("\nTop 5 templates:\n")

    for item in sorted(templates, key=lambda x: x["size"], reverse=True)[:5]:
        print(f"Cluster : {item['cluster_id']}")
        print(f"Count   : {item['count']} ({item['frequency']}%)")
        print(f"Template: {item['template']}\n")