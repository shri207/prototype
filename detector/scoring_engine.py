import re
from typing import Any, Dict, Tuple


# Severity keyword weight mapping
CRITICAL_KEYWORDS = ["fatal", "emergency", "emerg", "panic", "tamper", "attack", "corrupt", "unauthorized"]
HIGH_KEYWORDS = ["error", "authentication failure", "failed password", "user unknown", "denied", "exception", "broken pipe", "segfault", "exited abnormally"]
MEDIUM_KEYWORDS = ["warn", "warning", "delete", "replicate", "session opened", "su(pam_unix)", "connection refused", "timeout"]
LOW_KEYWORDS = ["notice", "info", "debug", "terminating", "success", "session closed"]

# Suspicious behavior / pattern markers
SUSPICIOUS_BEHAVIORS = [
    r"\buid=0\b",
    r"\beuid=0\b",
    r"\buser=root\b",
    r"/etc/\w+",
    r"delete\s+blk_",
    r"replicate\s+blk_",
    r"transfer\s+block",
    r"\bNODEVssh\b",
    r"\bscoreboard slot\b"
]


def calculate_frequency_score(frequency: float, count: int) -> Tuple[int, str]:
    """
    Computes frequency score from 0 to 40.
    Rarer events receive higher scores.
    """
    if frequency <= 0.05:
        score = 40
        reason = f"Extremely rare occurrence ({frequency:.2f}%, {count} event(s))"
    elif frequency <= 0.10:
        score = 35
        reason = f"Very rare occurrence ({frequency:.2f}%, {count} event(s))"
    elif frequency <= 0.50:
        score = 28
        reason = f"Low frequency occurrence ({frequency:.2f}%, {count} event(s))"
    elif frequency <= 1.50:
        score = 18
        reason = f"Moderate frequency ({frequency:.2f}%, {count} event(s))"
    elif frequency <= 5.00:
        score = 10
        reason = f"Occasional occurrence ({frequency:.2f}%, {count} event(s))"
    elif frequency <= 15.00:
        score = 4
        reason = f"Common occurrence ({frequency:.2f}%, {count} event(s))"
    else:
        score = 0
        reason = f"Baseline recurring traffic ({frequency:.2f}%, {count} event(s))"

    return score, reason


def calculate_novelty_score(template: str, signature: str, cluster_count: int) -> Tuple[int, str]:
    """
    Computes novelty score from 0 to 25 based on structural variance,
    token complexity, and signature uniqueness.
    """
    score = 5  # Base novelty

    wildcards = template.count("<*>")
    tokens = template.split()
    token_count = len(tokens) if tokens else 1

    # High ratio of wildcards or unusual parameterization
    wildcard_ratio = wildcards / token_count if token_count > 0 else 0
    if wildcard_ratio > 0.4:
        score += 8
    elif wildcard_ratio > 0.2:
        score += 5

    # Complex structural signature
    sig_tokens = signature.split() if signature else []
    if any(t in sig_tokens for t in ("BLOCK_ID", "KEY_VALUE_IP", "PATH", "USER")):
        score += 6

    # Cluster distinctness
    if cluster_count <= 2:
        score += 6
    elif cluster_count <= 5:
        score += 3

    score = min(25, max(0, score))
    reason = f"Structural signature with {wildcards} variable parameters and specialized token types"
    return score, reason


def calculate_severity_score(template: str, raw_samples: list) -> Tuple[int, str]:
    """
    Computes severity score from 0 to 20 based on security keywords
    and status codes in the template and sample lines.
    """
    text = (template + " " + " ".join(str(s) for s in raw_samples[:3])).lower()

    for kw in CRITICAL_KEYWORDS:
        if kw in text:
            return 20, f"Critical security/system keyword match: '{kw}'"

    for kw in HIGH_KEYWORDS:
        if kw in text:
            return 16, f"High-risk error/auth indicator match: '{kw}'"

    for kw in MEDIUM_KEYWORDS:
        if kw in text:
            return 10, f"Medium warning or administrative operation match: '{kw}'"

    for kw in LOW_KEYWORDS:
        if kw in text:
            return 3, f"Standard informational or low-severity marker: '{kw}'"

    return 2, "Standard log level without elevated severity markers"


def calculate_behavior_score(template: str, raw_samples: list) -> Tuple[int, str]:
    """
    Computes behavior/pattern score from 0 to 15 based on access patterns,
    privilege indicators, and unusual operations.
    """
    text = template + " " + " ".join(str(s) for s in raw_samples[:3])
    score = 0
    matches = []

    for pattern in SUSPICIOUS_BEHAVIORS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 5
            matches.append(pattern)

    score = min(15, score)
    if score > 0:
        reason = f"Behavioral pattern matches: {', '.join(matches[:2])}"
    else:
        reason = "Standard system behavior pattern"

    return score, reason


def map_score_to_risk(score: int) -> str:
    """
    Maps numeric score (0-100) to risk categories:
    0–29   LOW
    30–59  MEDIUM
    60–79  HIGH
    80–100 CRITICAL
    """
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def evaluate_cluster_risk(
    cluster: Dict[str, Any],
    raw_samples: list = None
) -> Dict[str, Any]:
    """
    Performs comprehensive explainable risk scoring on a template cluster.
    Returns complete breakdown across all 4 factors, total score, and mapped risk.
    """
    if raw_samples is None:
        raw_samples = []

    template = cluster.get("template", "")
    frequency = cluster.get("frequency", 0.0)
    count = cluster.get("count", cluster.get("size", 1))
    signature = cluster.get("signature", "")

    freq_score, freq_reason = calculate_frequency_score(frequency, count)
    nov_score, nov_reason = calculate_novelty_score(template, signature, count)
    sev_score, sev_reason = calculate_severity_score(template, raw_samples)
    beh_score, beh_reason = calculate_behavior_score(template, raw_samples)

    total_score = min(100, freq_score + nov_score + sev_score + beh_score)
    risk_level = map_score_to_risk(total_score)

    # Confidence calculation based on multi-signal convergence
    active_signals = sum(1 for s in (freq_score > 15, sev_score > 5, beh_score > 0, nov_score > 10) if s)
    confidence = round(0.70 + (active_signals * 0.06), 2)
    confidence = min(0.96, confidence)

    # Synthesize comprehensive explainability reason
    reasons = [freq_reason, sev_reason]
    if beh_score > 0:
        reasons.append(beh_reason)
    explanation = ". ".join(reasons) + "."

    return {
        "cluster_id": cluster.get("cluster_id", "C000"),
        "risk": risk_level,
        "risk_score": total_score,
        "confidence": confidence,
        "breakdown": {
            "frequency_score": freq_score,
            "novelty_score": nov_score,
            "severity_score": sev_score,
            "behavior_score": beh_score
        },
        "explanations": {
            "frequency": freq_reason,
            "novelty": nov_reason,
            "severity": sev_reason,
            "behavior": beh_reason
        },
        "reason": explanation
    }
