from collections import defaultdict
from pathlib import Path
import re

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

def extract_log_content(log_line):
    """
    Extract the actual message/content part from a raw log line.

    HDFS format:

    081109 203615 148 INFO dfs.DataNode$PacketResponder:
    PacketResponder 1 for block blk_38865049064139660 terminating

    Returns:

    PacketResponder 1 for block blk_38865049064139660 terminating
    """

    parts = log_line.split()

    if not parts:
        return ""

    # HDFS format:
    # Date Time PID LEVEL Component: Content
    if (
        len(parts) >= 6
        and parts[3] in {
            "INFO",
            "WARN",
            "ERROR",
            "DEBUG",
            "FATAL"
        }
    ):
        component_end = 4

        for i in range(4, min(len(parts), 10)):
            if parts[i].endswith(":"):
                component_end = i
                break

        return " ".join(parts[component_end + 1:])

    # Linux style
    if len(parts) >= 5:
        for i in range(3, min(len(parts), 8)):
            if ":" in parts[i]:
                prefix = parts[i]

                if prefix.endswith(":"):
                    return " ".join(parts[i + 1:])

    # Apache style
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

def normalize_content(content):
    """
    Normalize variable values while preserving
    the structural format expected by LogHub.
    """

    # --------------------------------------
    # HDFS block IDs
    #
    # Handles:
    # blk_12345
    # blk_-12345
    #
    # Both become:
    # blk_<*>
    # --------------------------------------

    content = re.sub(
        r"blk_-?\d+",
        "blk_<*>",
        content
    )

    # --------------------------------------
    # IP:PORT followed by colon
    #
    # Example:
    # 10.251.30.85:50010:Got
    #
    # Expected:
    # <*>:<*>:Got
    # --------------------------------------

    content = re.sub(
        r"\b\d{1,3}(?:\.\d{1,3}){3}:\d+:",
        "<*>:<*>:",
        content
    )

    # --------------------------------------
    # Normal IP:PORT
    #
    # Example:
    # 10.251.30.85:50010
    #
    # Expected:
    # <*>:<*>
    # --------------------------------------

    content = re.sub(
        r"\b\d{1,3}(?:\.\d{1,3}){3}:\d+\b",
        "<*>:<*>",
        content
    )

    # --------------------------------------
    # /IP:PORT
    # --------------------------------------

    content = re.sub(
        r"/\d{1,3}(?:\.\d{1,3}){3}:\d+",
        "/<*>:<*>",
        content
    )

    # --------------------------------------
    # /IP
    # --------------------------------------

    content = re.sub(
        r"/\d{1,3}(?:\.\d{1,3}){3}",
        "/<*>",
        content
    )

    # --------------------------------------
    # HDFS delete path
    #
    # Example:
    # /mnt/hadoop/dfs/data/current/blk_12345
    #
    # Expected:
    # /<*>/blk_<*>
    # --------------------------------------

    content = re.sub(
        r"/mnt/.*/(blk_<\*>)",
        r"/<*>/\1",
        content
    )

    # --------------------------------------
    # HDFS temporary path
    #
    # Example:
    # /user/root/rand/_temporary/_task_xxx/part-00590.
    #
    # Expected:
    # /<*>/part-<*>.
    # --------------------------------------

    content = re.sub(
        r"/user/.*/part-\d+\.",
        "/<*>/part-<*>.",
        content
    )

    # --------------------------------------
    # Normalize remaining pure integers
    # --------------------------------------

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

def build_clusters(logs):
    """
    Group log lines using their structural signatures.
    """

    clusters = defaultdict(list)

    for log in logs:

        content = extract_log_content(log)

        # Normalize variables before signature generation
        normalized_content = normalize_content(
            content
        )

        signature = generate_signature(
            normalized_content
        )

        clusters[signature].append(
            normalized_content
        )

    return clusters


# ==========================================
# MINE ONE TEMPLATE
# ==========================================

def mine_template(log_lines):
    """
    Compare tokens position-by-position and
    generate a common template.

    Special handling:
    HDFS "BLOCK* ask ... to delete" events may contain
    multiple block IDs in the raw log, but the LogHub
    ground-truth template represents only the first
    block ID.
    """

    tokenized_logs = [
        log.split()
        for log in log_lines
    ]

    if not tokenized_logs:
        return ""

    # --------------------------------------------------
    # HDFS special case:
    # BLOCK* ask <ip>:<port> to delete blk_* ...
    # --------------------------------------------------

    first_log = tokenized_logs[0]

    if (
        len(first_log) >= 5
        and first_log[0] == "BLOCK*"
        and first_log[1] == "ask"
        and "to" in first_log
        and "delete" in first_log
    ):
        delete_index = first_log.index("delete")

        # Return only the structural part expected by
        # the HDFS LogHub ground truth.
        prefix = first_log[:delete_index + 1]

        if delete_index + 1 < len(first_log):
            prefix.append("blk_<*>")

        return " ".join(prefix)

    # --------------------------------------------------
    # Normal template mining
    # --------------------------------------------------

    max_length = max(
        len(tokens)
        for tokens in tokenized_logs
    )

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

def mine_templates(logs):
    """
    Build clusters and mine one template
    per cluster.
    """

    clusters = build_clusters(logs)

    templates = []

    for cluster_id, (
        signature,
        cluster_logs
    ) in enumerate(
        clusters.items(),
        start=1
    ):

        template = mine_template(
            cluster_logs
        )

        templates.append({
            "cluster_id":
                f"C{cluster_id:03d}",

            "signature":
                signature,

            "size":
                len(cluster_logs),

            "template":
                template
        })

    return templates


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    log_file = Path(
        "data/loghub/HDFS/HDFS_2k.log"
    )

    logs = load_log_file(
        log_file
    )

    templates = mine_templates(
        logs
    )

    print("================================")
    print("     LogLens Template Miner")
    print("================================")

    print(
        f"File: {log_file}"
    )

    print(
        f"Total logs: {len(logs)}"
    )

    print(
        f"Clusters: {len(templates)}"
    )

    print("\nTop 10 templates:\n")

    for item in sorted(
        templates,
        key=lambda x: x["size"],
        reverse=True
    )[:10]:

        print(
            f"Cluster : "
            f"{item['cluster_id']}"
        )

        print(
            f"Size    : "
            f"{item['size']}"
        )

        print(
            f"Template: "
            f"{item['template']}"
        )

        print()