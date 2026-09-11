import re
from typing import List, Union
from pathlib import Path


# Regex patterns for structural log format detection
HDFS_PATTERN = re.compile(
    r"^\d{6}\s+\d{6}\s+\d+\s+(INFO|WARN|ERROR|DEBUG|FATAL)\s+dfs\.",
    re.IGNORECASE
)
HDFS_KEYWORD_PATTERN = re.compile(
    r"\b(dfs\.DataNode|dfs\.FSNamesystem|PacketResponder|BLOCK\*|blk_-?\d+)\b"
)

APACHE_ERROR_PATTERN = re.compile(
    r"^\[(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4}\]\s+\[(notice|error|warn|info|debug|crit|alert|emerg)\]",
    re.IGNORECASE
)
APACHE_ACCESS_PATTERN = re.compile(
    r"^\d{1,3}(?:\.\d{1,3}){3}\s+-\s+-\s+\[\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}",
    re.IGNORECASE
)

LINUX_SYSLOG_PATTERN = re.compile(
    r"^[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+[\w\.\-]+(?:\s+[\w\.\-]+)?(?:\([\w\-]+\))?\[?\d*\]?:",
    re.IGNORECASE
)
LINUX_SERVICE_PATTERN = re.compile(
    r"\b(sshd|pam_unix|su|sudo|logrotate|kernel|systemd|cron|authpriv)\b",
    re.IGNORECASE
)


def detect_log_source(
    logs: Union[List[str], str, Path],
    max_sample_lines: int = 50
) -> str:
    """
    Identifies whether the input logs resemble HDFS, Linux, Apache, or Generic.
    Detection is based on structural regex patterns, syslog headers, and characteristic tokens,
    not merely the filename.
    """
    sample_lines = []

    if isinstance(logs, (str, Path)):
        path = Path(logs)
        if path.exists() and path.is_file():
            # Check filename as a fallback hint
            filename_lower = path.name.lower()
            if "hdfs" in filename_lower:
                filename_hint = "HDFS"
            elif "linux" in filename_lower or "syslog" in filename_lower or "auth" in filename_lower:
                filename_hint = "Linux"
            elif "apache" in filename_lower or "httpd" in filename_lower:
                filename_hint = "Apache"
            else:
                filename_hint = None

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        sample_lines.append(stripped)
                        if len(sample_lines) >= max_sample_lines:
                            break
        else:
            # Maybe raw log string with newlines
            sample_lines = [l.strip() for l in str(logs).splitlines() if l.strip()][:max_sample_lines]
            filename_hint = None
    elif isinstance(logs, list):
        filename_hint = None
        for item in logs:
            if isinstance(item, str) and item.strip():
                sample_lines.append(item.strip())
            elif isinstance(item, dict) and "raw_log" in item:
                sample_lines.append(item["raw_log"].strip())
            if len(sample_lines) >= max_sample_lines:
                break
    else:
        return "Generic"

    if not sample_lines:
        return filename_hint if filename_hint else "Generic"

    hdfs_score = 0
    apache_score = 0
    linux_score = 0

    for line in sample_lines:
        # Check HDFS
        if HDFS_PATTERN.search(line) or HDFS_KEYWORD_PATTERN.search(line):
            hdfs_score += 2
        elif "INFO" in line or "WARN" in line:
            if re.match(r"^\d{6}\s+\d{6}", line):
                hdfs_score += 1

        # Check Apache
        if APACHE_ERROR_PATTERN.search(line) or APACHE_ACCESS_PATTERN.search(line):
            apache_score += 2
        elif line.startswith("[") and ("] [notice]" in line or "] [error]" in line or "] [warn]" in line):
            apache_score += 2

        # Check Linux
        if LINUX_SYSLOG_PATTERN.search(line):
            linux_score += 2
        if LINUX_SERVICE_PATTERN.search(line):
            linux_score += 1

    scores = {
        "HDFS": hdfs_score,
        "Apache": apache_score,
        "Linux": linux_score
    }

    best_source = max(scores, key=scores.get)
    best_score = scores[best_source]

    # If evidence found, return detected source
    if best_score >= 2:
        return best_source

    if filename_hint:
        return filename_hint

    return "Generic"
