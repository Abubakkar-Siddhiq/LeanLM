ROUTING_RULES = [
    {
        "task_types": ["simple_qa", "summarization", "extraction", "writing"],
        "complexities": ["low"],
        "model": "llama-3.1-8b-instant",
        "reason": "Simple factual tasks routed to fast, cheap model.",
    },
    {
        "task_types": ["coding", "debugging"],
        "complexities": ["medium"],
        "model": "qwen/qwen3-32b",
        "reason": "Coding and debugging tasks routed to medium-capability model.",
    },
    {
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

FALLBACK_MODEL_BY_COMPLEXITY = {
    "low": [
        "llama-3.1-8b-instant",
        "qwen/qwen3-32b",
    ],
    "medium": [
        "qwen/qwen3-32b",
        "openai/gpt-oss-120b",
        "llama-3.1-8b-instant",
    ],
    "high": [
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b",
    ],
}
