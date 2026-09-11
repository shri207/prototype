import re


def tokenize_log(log_line):
    """
    Convert a raw log line into individual tokens.
    """

    tokens = log_line.split()

    return tokens


def classify_token(token):
    """
    Identify the structural type of a token.
    """

    # Remove common punctuation around the token
    clean_token = token.strip("[](),;:")

    if re.fullmatch(r"\d+", clean_token):
        return "NUMBER"

    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", clean_token):
        return "IP"

    if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}", clean_token):
        return "TIME"

    if clean_token.startswith("blk_"):
        return "BLOCK_ID"

    if clean_token.startswith("/") or "\\" in clean_token:
        return "PATH"

    if "=" in clean_token:
        key, value = clean_token.split("=", 1)

        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", value):
            return "KEY_VALUE_IP"

        if re.fullmatch(r"\d+", value):
            return "KEY_VALUE_NUMBER"

        return "KEY_VALUE"

    return "WORD" 


def analyze_log_line(log_line):
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