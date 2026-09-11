from pathlib import Path
import sys
import pandas as pd

# ==========================================
# PROJECT ROOT
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from parser.loader import load_log_file
from parser.template_miner import (
    mine_templates,
    extract_log_content,
    normalize_content
)


# ==========================================
# VARIABLE
# ==========================================

VARIABLE = "<*>"


# ==========================================
# LOAD GROUND TRUTH
# ==========================================

def load_ground_truth(csv_path):
    """
    Load LogHub structured ground-truth CSV.
    """

    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {path}"
        )

    return pd.read_csv(path)


# ==========================================
# NORMALIZE TEMPLATE
# ==========================================

def normalize_template(template):
    """
    Normalize whitespace.
    """

    if pd.isna(template):
        return ""

    return " ".join(
        str(template).split()
    )


# ==========================================
# PREDICT TEMPLATE
# ==========================================

def predict_template(log_line):
    """
    Convert one raw log line into a normalized
    event template.

    Uses the same normalization logic as
    template_miner.py.
    """

    content = extract_log_content(log_line)

    normalized = normalize_content(content)

    # --------------------------------------------------
    # HDFS special case:
    #
    # BLOCK* ask <ip>:<port> to delete blk_<*>
    #
    # Some HDFS logs contain multiple block IDs after
    # "delete", but LogHub represents this event using
    # only the first block ID.
    # --------------------------------------------------

    tokens = normalized.split()

    if (
        len(tokens) >= 5
        and tokens[0] == "BLOCK*"
        and tokens[1] == "ask"
        and "to" in tokens
        and "delete" in tokens
    ):
        delete_index = tokens.index("delete")

        prefix = tokens[:delete_index + 1]

        if delete_index + 1 < len(tokens):
            prefix.append("blk_<*>")

        return " ".join(prefix)

    return normalized

# ==========================================
# EVALUATION
# ==========================================

def evaluate_parser(
    log_file,
    ground_truth_file
):
    """
    Compare LogLens predicted templates
    with LogHub ground-truth EventTemplate.
    """

    print("================================")
    print("      LogLens Evaluation")
    print("================================")

    # --------------------------------------
    # Load raw logs
    # --------------------------------------

    logs = load_log_file(
        log_file
    )

    # --------------------------------------
    # Load ground truth
    # --------------------------------------

    ground_truth = load_ground_truth(
        ground_truth_file
    )

    # --------------------------------------
    # Dataset size
    # --------------------------------------

    total = min(
        len(logs),
        len(ground_truth)
    )

    print(
        f"Log file       : {log_file}"
    )

    print(
        f"Ground truth   : {ground_truth_file}"
    )

    print(
        f"Total evaluated: {total}"
    )

    # --------------------------------------
    # Mine templates
    # --------------------------------------

    mined_templates = mine_templates(
        logs
    )

    print(
        f"Mined clusters : "
        f"{len(mined_templates)}"
    )

    # --------------------------------------
    # Create results
    # --------------------------------------

    results = []

    correct = 0

    for index in range(total):

        log_line = logs[index]

        # ----------------------------------
        # Predicted template
        # ----------------------------------

        predicted = normalize_template(
            predict_template(
                log_line
            )
        )

        # ----------------------------------
        # Actual template
        # ----------------------------------

        actual = normalize_template(
            ground_truth.iloc[index][
                "EventTemplate"
            ]
        )

        # ----------------------------------
        # Compare
        # ----------------------------------

        is_correct = (
            predicted == actual
        )

        if is_correct:
            correct += 1

        results.append({
            "LineId":
                ground_truth.iloc[index][
                    "LineId"
                ],

            "PredictedTemplate":
                predicted,

            "ActualTemplate":
                actual,

            "Correct":
                is_correct
        })

    # --------------------------------------
    # Accuracy
    # --------------------------------------

    incorrect = total - correct

    accuracy = (
        correct / total * 100
        if total > 0
        else 0
    )

    return (
        accuracy,
        results,
        len(mined_templates)
    )


# ==========================================
# PRINT RESULTS
# ==========================================

def print_results(
    log_file,
    ground_truth_file,
    accuracy,
    results,
    cluster_count
):
    """
    Display evaluation results.
    """

    correct = sum(
        1
        for result in results
        if result["Correct"]
    )

    incorrect = (
        len(results) - correct
    )

    print()

    print("================================")
    print("      LogLens Evaluation")
    print("================================")

    print(
        f"Log file       : {log_file}"
    )

    print(
        f"Ground truth   : {ground_truth_file}"
    )

    print(
        f"Total evaluated: "
        f"{len(results)}"
    )

    print(
        f"Mined clusters : "
        f"{cluster_count}"
    )

    print(
        f"Correct        : "
        f"{correct}"
    )

    print(
        f"Incorrect      : "
        f"{incorrect}"
    )

    print(
        f"Accuracy       : "
        f"{accuracy:.2f}%"
    )

    # --------------------------------------
    # First 10 comparisons
    # --------------------------------------

    print()
    print("First 10 comparisons:")
    print()

    for result in results[:10]:

        print(
            f"Line {result['LineId']}"
        )

        print(
            f"Predicted : "
            f"{result['PredictedTemplate']}"
        )

        print(
            f"Actual    : "
            f"{result['ActualTemplate']}"
        )

        print(
            f"Match     : "
            f"{result['Correct']}"
        )

        print(
            "-" * 60
        )

    # --------------------------------------
    # First 10 errors
    # --------------------------------------

    errors = [
        result
        for result in results
        if not result["Correct"]
    ]

    print()
    print("================================")
    print("       First 10 Errors")
    print("================================")

    print()

    for result in errors[:10]:

        print(
            f"Line {result['LineId']}"
        )

        print(
            f"Predicted : "
            f"{result['PredictedTemplate']}"
        )

        print(
            f"Actual    : "
            f"{result['ActualTemplate']}"
        )

        print(
            f"Match     : "
            f"{result['Correct']}"
        )

        print(
            "-" * 60
        )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    log_file = (
        PROJECT_ROOT
        / "data"
        / "loghub"
        / "HDFS"
        / "HDFS_2k.log"
    )

    ground_truth_file = (
        PROJECT_ROOT
        / "data"
        / "loghub"
        / "HDFS"
        / "HDFS_2k.log_structured.csv"
    )

    accuracy, results, cluster_count = (
        evaluate_parser(
            log_file,
            ground_truth_file
        )
    )

    print_results(
        log_file,
        ground_truth_file,
        accuracy,
        results,
        cluster_count
    )