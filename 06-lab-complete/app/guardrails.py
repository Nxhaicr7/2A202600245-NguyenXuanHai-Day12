import re
from .config import settings

# Allowed banking topics
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]

def detect_injection(user_input: str) -> bool:
    """Detect prompt injection patterns."""
    patterns = [
        r"ignore (all )?(previous|above) instructions",
        r"you are now",
        r"system prompt",
        r"reveal your (instructions|prompt)",
        r"pretend you are",
        r"act as (a |an )?unrestricted",
        r"dan mode",
    ]
    for pattern in patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return True
    return False

def topic_filter(user_input: str) -> bool:
    """Check if input is off-topic or contains blocked topics.
    
    Returns:
        True if input should be BLOCKED.
    """
    input_lower = user_input.lower()

    # 1. Blocked topics
    if any(blocked in input_lower for blocked in BLOCKED_TOPICS):
        return True

    # 2. Allowed topics check
    # In a real app, this might be more complex (e.g., using an LLM or embeddings)
    # For this lab, we check if at least one banking keyword is present
    if any(allowed in input_lower for allowed in ALLOWED_TOPICS):
        return False

    # Default to blocked if no allowed topics found
    return True
