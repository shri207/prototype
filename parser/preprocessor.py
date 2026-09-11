import re
from typing import Any, Dict, List


HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def tokenize_log(log_line: str) -> List[str]:
    """
    Convert a raw log line into individual tokens.
    """
    return log_line.split()


def classify_token(token: str) -> str:
    """
    Identify the structural type of a token.
    """
    # Remove common punctuation around the token
    clean_token = token.strip("[](),;:\"'")

    if clean_token in HTTP_METHODS:
        return "HTTP_METHOD"

    if clean_token.startswith("blk_"):
        return "BLOCK_ID"

    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", clean_token):
        return "IP"

    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+:\d+", clean_token):
        return "IP_PORT"

    if re.fullmatch(r":\d+", clean_token):
        return "PORT"

    if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}", clean_token):
        return "TIME"

    if clean_token.startswith("/") or "\\" in clean_token:
        return "PATH"

    if "=" in clean_token:
        key, value = clean_token.split("=", 1)
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", value):
            return "KEY_VALUE_IP"
        if re.fullmatch(r"\d+", value):
            return "KEY_VALUE_NUMBER"
        if key.lower() in ("user", "uid", "euid", "ruser", "logname"):
            return "USER"
        return "KEY_VALUE"

    if re.fullmatch(r"\d+", clean_token):
        if len(clean_token) == 3 and clean_token in ("200", "201", "204", "301", "302", "304", "400", "401", "403", "404", "500", "502", "503"):
            return "STATUS_CODE"
        return "NUMBER"

    return "WORD"


def analyze_log_line(log_line: str) -> List[Dict[str, str]]:
    """
    Tokenize a log line and classify every token.
    """
    tokens = tokenize_log(log_line)
    analyzed_tokens = []
    for token in tokens:
        analyzed_tokens.append({
            "token": token,
            "type": classify_token(token)
        })
    return analyzed_tokens


if __name__ == "__main__":
    sample_log = (
        "Jun 14 15:16:01 combo "
        "sshd(pam_unix)[19939]: "
        "authentication failure; logname= uid=0 euid=0 "
        "tty=NODEVssh ruser= rhost=218.188.2.4"
    )

    result = analyze_log_line(sample_log)
    print("================================")
    print("     LogLens Preprocessor")
    print("================================")
    for item in result:
        print(f"{item['token']:45} -> {item['type']}")