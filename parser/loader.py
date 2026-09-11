from pathlib import Path
import re
from typing import Dict, List, Optional, Union

try:
    from .source_detector import detect_log_source
except ImportError:
    from source_detector import detect_log_source


class LogFormatError(Exception):
    """Raised when log data is corrupted or unsupported."""
    pass


def extract_timestamp(log_line: str, source: str) -> Optional[str]:
    """
    Extracts timestamp from log lines based on source format.
    """
    if source == "HDFS":
        match = re.match(r"^(\d{6}\s+\d{6})", log_line)
        if match:
            return match.group(1)
    elif source == "Apache":
        match = re.search(r"\[([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})\]", log_line)
        if match:
            return match.group(1)
    elif source == "Linux":
        match = re.match(r"^([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})", log_line)
        if match:
            return match.group(1)

    # Generic fallback search for standard date/time
    match = re.search(r"\b(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?|\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2})\b", log_line)
    if match:
        return match.group(1)

    return None


def load_log_file(
    file_path: Union[str, Path],
    return_records: bool = False
) -> Union[List[str], List[Dict[str, Union[int, str]]]]:
    """
    Reads a log file, cleans empty lines, and returns either a list of raw strings
    (for backwards compatibility) or a list of structured log records.

    :param file_path: Path to log file
    :param return_records: If True, returns list of dicts with keys (line_id, raw_log, source, timestamp)
    :raises FileNotFoundError: If file does not exist
    :raises LogFormatError: If file is empty or unreadable
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    if not path.is_file():
        raise LogFormatError(f"Specified path is not a file: {file_path}")

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
    except Exception as e:
        raise LogFormatError(f"Failed to read file '{file_path}': {str(e)}")

    clean_lines = [line.strip() for line in lines if line.strip()]

    if not clean_lines:
        raise LogFormatError(f"Log file '{file_path}' is empty or contains only whitespace.")

    if not return_records:
        return clean_lines

    source = detect_log_source(path)
    records: List[Dict[str, Union[int, str]]] = []

    for line_id, raw_line in enumerate(clean_lines, start=1):
        ts = extract_timestamp(raw_line, source)
        records.append({
            "line_id": line_id,
            "raw_log": raw_line,
            "source": source,
            "timestamp": ts or f"L{line_id}"
        })

    return records


def load_log_records(file_path: Union[str, Path]) -> List[Dict[str, Union[int, str]]]:
    """Convenience helper to always return structured log records."""
    return load_log_file(file_path, return_records=True)


if __name__ == "__main__":
    log_file = "data/loghub/Linux/Linux_2k.log"
    records = load_log_records(log_file)
    print("================================")
    print("       LogLens Log Loader")
    print("================================")
    print(f"File: {log_file}")
    print(f"Detected source: {records[0]['source']}")
    print(f"Total log lines: {len(records)}")
    print("\nFirst 3 records:\n")
    for r in records[:3]:
        print(r)