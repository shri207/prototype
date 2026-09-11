from collections import Counter

try:
    from .preprocessor import analyze_log_line
    from .loader import load_log_file
except ImportError:
    from preprocessor import analyze_log_line
    from loader import load_log_file


def generate_signature(log_line):
    """
    Generate a structural signature for a log line.
    """

    analyzed_tokens = analyze_log_line(log_line)

    signature = [
        item["type"]
        for item in analyzed_tokens
    ]

    return " ".join(signature)


def analyze_dataset(file_path):
    """
    Generate structural signatures for every log line
    and count how frequently each signature occurs.
    """

    logs = load_log_file(file_path)

    signatures = []

    for log in logs:

        signature = generate_signature(log)

        signatures.append(signature)

    signature_counts = Counter(signatures)

    return logs, signature_counts


if __name__ == "__main__":

    log_file = "data/loghub/Linux/Linux_2k.log"

    logs, signature_counts = analyze_dataset(log_file)

    print("================================")
    print("  LogLens Dataset Analyzer")
    print("================================")

    print(f"File: {log_file}")
    print(f"Total logs: {len(logs)}")
    print(f"Unique signatures: {len(signature_counts)}")

    print("\nTop 10 structural signatures:\n")

    for signature, count in signature_counts.most_common(10):

        print(
            f"{count:5}  ->  {signature}"
        )