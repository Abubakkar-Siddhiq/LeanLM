"""Intent classifier evaluation script.

Run from the src/ directory:
    cd src; python ..\\tests\\intent_eval.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from providers.groq import GroqProvider
from services.routing import IntentClassifier

TEST_CASES = [
    {
        "prompt": "What is a variable?",
        "task_type": "simple_qa",
        "complexity": "low",
    },
    {
        "prompt": "Write a Python function to check palindrome",
        "task_type": "coding",
        "complexity": "medium",
    },
    {
        "prompt": "Fix this FastAPI validation error",
        "task_type": "debugging",
        "complexity": "medium",
    },
    {
        "prompt": "Design a scalable payment system with retries and idempotency",
        "task_type": "reasoning",
        "complexity": "high",
    },
    {
        "prompt": "Summarize this paragraph in one line",
        "task_type": "summarization",
        "complexity": "low",
    },
    {
        "prompt": "Extract name and email from this text as JSON",
        "task_type": "extraction",
        "complexity": "low",
    },
    {
        "prompt": "Rewrite this LinkedIn post professionally",
        "task_type": "writing",
        "complexity": "medium",
    },
]


async def evaluate():
    provider = GroqProvider()
    classifier = IntentClassifier(
        llm_provider=provider,
        classify_model="llama-3.1-8b-instant",
    )

    results = []
    total = len(TEST_CASES)

    print(f"Running {total} test cases through IntentClassifier...\n")

    for i, tc in enumerate(TEST_CASES, 1):
        prompt = tc["prompt"]
        exp_type = tc["task_type"]
        exp_complexity = tc["complexity"]

        print(f"  [{i}/{total}] classifying...", flush=True)
        result = await classifier.classify(prompt)

        act_type = result.task_type
        act_complexity = result.complexity
        type_match = act_type == exp_type
        complexity_match = act_complexity == exp_complexity
        overall = type_match and complexity_match

        results.append({
            "prompt": prompt,
            "task_type": exp_type,
            "act_type": act_type,
            "exp_complexity": exp_complexity,
            "act_complexity": act_complexity,
            "confidence": result.confidence,
            "reason": result.reason,
            "type_match": type_match,
            "complexity_match": complexity_match,
            "overall": overall,
        })

        print(
            f"    type: {exp_type} -> {act_type} "
            f"({'PASS' if type_match else 'FAIL'}), "
            f"complexity: {exp_complexity} -> {act_complexity} "
            f"({'PASS' if complexity_match else 'FAIL'}), "
            f"confidence={result.confidence}"
        )

    # Summary Table
    passed_complexity = sum(1 for r in results if r["complexity_match"])
    passed_type = sum(1 for r in results if r["type_match"])
    passed_overall = sum(1 for r in results if r["overall"])

    print()
    print("=" * 120)
    print("INTENT CLASSIFIER EVALUATION RESULTS")
    print("=" * 120)
    print()
    header = (
        f"{'Prompt':<50} {'Type':<14} {'ActType':<14} "
        f"{'ExpC':<5} {'ActC':<5} {'Conf':<6} {'Type?':<7} {'Cmp?':<7}"
    )
    print(header)
    print("-" * 120)
    for r in results:
        p = r["prompt"][:49] if len(r["prompt"]) > 49 else r["prompt"]
        print(
            f"{p:<50} {r['task_type']:<14} {r['act_type']:<14} "
            f"{r['exp_complexity']:<5} {r['act_complexity']:<5} "
            f"{r['confidence']:<6.2f} "
            f"{'PASS' if r['type_match'] else 'FAIL':<7} "
            f"{'PASS' if r['complexity_match'] else 'FAIL':<7}"
        )
    print("-" * 120)
    print(f"\n  task_type accuracy:   {passed_type}/{total} = {passed_type/total*100:.1f}%")
    print(f"  complexity accuracy: {passed_complexity}/{total} = {passed_complexity/total*100:.1f}%")
    print(f"  overall accuracy:    {passed_overall}/{total} = {passed_overall/total*100:.1f}%")

    # Breakdown by complexity level
    print()
    for level in ["low", "medium", "high"]:
        cases = [r for r in results if r["exp_complexity"] == level]
        c_pass = sum(1 for r in cases if r["complexity_match"])
        if cases:
            print(
                f"  complexity '{level}': {c_pass}/{len(cases)} "
                f"({c_pass/len(cases)*100:.1f}%)"
            )

    # Breakdown by task_type
    print()
    types = sorted(set(r["task_type"] for r in results))
    for t in types:
        cases = [r for r in results if r["task_type"] == t]
        t_pass = sum(1 for r in cases if r["type_match"])
        print(
            f"  task_type '{t}': {t_pass}/{len(cases)} "
            f"({t_pass/len(cases)*100:.1f}%)"
        )

    # Mismatches detail
    mismatches = [r for r in results if not r["overall"]]
    if mismatches:
        print()
        print("MISMATCHES:")
        for r in mismatches:
            print(f"  - task_type: {r['task_type']} != {r['act_type']} | "
                  f"complexity: {r['exp_complexity']} != {r['act_complexity']} | "
                  f"\"{r['prompt'][:60]}\"")
            print(f"    reason: {r['reason']}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(evaluate())
