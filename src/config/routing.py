ROUTING_RULES = [
    {
        "provider": "groq",
        "task_types": ["simple_qa", "summarization", "extraction", "writing"],
        "complexities": ["low"],
        "model": "llama-3.1-8b-instant",
        "reason": "Simple factual tasks routed to fast, cheap model.",
    },
    {
        "provider": "groq",
        "task_types": ["coding", "debugging"],
        "complexities": ["medium"],
        "model": "qwen/qwen3-32b",
        "reason": "Coding and debugging tasks routed to medium-capability model.",
    },
    {
        "provider": "openai",
        "task_types": ["reasoning"],
        "complexities": ["high"],
        "model": "openai/gpt-oss-120b",
        "reason": "Complex reasoning tasks routed to most capable model.",
    },
]

DEFAULT_MODEL_BY_COMPLEXITY = {
    "low": "llama-3.1-8b-instant",
    "medium": "qwen/qwen3-32b",
    "high": "openai/gpt-oss-120b",
}

MODEL_TO_PROVIDER = {
    "llama-3.1-8b-instant": "groq",
    "qwen/qwen3-32b": "groq",
    "openai/gpt-oss-120b": "openai",
    "gpt-4o-mini": "openai",
    "gpt-4o": "openai",
    "claude-sonnet-4-20250514": "anthropic",
    "claude-haiku-3-20240307": "anthropic",
    "gemini-2.0-flash": "google",
    "gemini-1.5-pro": "google",
}

FALLBACK_MODEL_BY_COMPLEXITY = {
    "low": [
        "llama-3.1-8b-instant",    # groq
        "qwen/qwen3-32b",          # groq
        "gpt-4o-mini",             # openai
        "gpt-4o",                  # openai
        "gemini-2.0-flash",        # google
        "claude-haiku-3-20240307", # anthropic
    ],
    "medium": [
        "qwen/qwen3-32b",          # groq
        "llama-3.1-8b-instant",   # groq
        "gpt-4o",                  # openai
        "gpt-4o-mini",             # openai
        "claude-sonnet-4-20250514",# anthropic
        "claude-haiku-3-20240307", # anthropic
        "gemini-2.0-flash",        # google
    ],
    "high": [
        "openai/gpt-oss-120b",     # openai
        "gpt-4o",                  # openai
        "claude-sonnet-4-20250514",# anthropic
        "gemini-1.5-pro",          # google
        "qwen/qwen3-32b",          # groq
    ],
}
