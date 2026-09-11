from pathlib import Path


def load_log_file(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        logs = [line.strip() for line in file if line.strip()]

    return logs


if __name__ == "__main__":
    log_file = "data/loghub/Linux/Linux_2k.log"

    logs = load_log_file(log_file)

    print("================================")
    print("       LogLens Log Loader")
    print("================================")
    print(f"File: {log_file}")
    print(f"Total log lines: {len(logs)}")

    print("\nFirst 5 log lines:\n")

    for i, log in enumerate(logs[:5], start=1):
        print(f"{i}. {log}")