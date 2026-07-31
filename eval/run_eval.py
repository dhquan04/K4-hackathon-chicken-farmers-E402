"""
Evaluation Runner Script
Evaluates FoodFlow AI Agent / Workflow accuracy against 20 Golden Set test cases.
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from project.codebase.workflow import handle_message, detect_intent

GOLDEN_SET_PATH = os.path.join(os.path.dirname(__file__), "golden_set.json")


def run_evaluation():
    if not os.path.exists(GOLDEN_SET_PATH):
        print(f"Error: Golden set file not found at {GOLDEN_SET_PATH}")
        return

    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"=== Running Evaluation on {len(cases)} Golden Set Test Cases ===")
    
    passed = 0
    failed = 0

    for case in cases:
        case_id = case["id"]
        user_input = case["input"]
        expected_tool = case["expected_tool"]
        desc = case["description"]

        detected = detect_intent(user_input)

        is_correct = (detected == expected_tool)
        if is_correct:
            passed += 1
            status_str = "[PASS]"
        else:
            failed += 1
            status_str = "[FAIL]"

        print(f"{status_str} Case #{case_id:02d}: {desc}")
        print(f"   Input: '{user_input}'")
        print(f"   Expected Tool: {expected_tool} | Detected: {detected}\n")

    accuracy = (passed / len(cases)) * 100
    print("=== EVALUATION SUMMARY ===")
    print(f"Total Cases: {len(cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Accuracy Rate: {accuracy:.1f}%\n")

    if accuracy >= 90.0:
        print("RESULT: QUALITY BAR MET (>= 90%)")
    else:
        print("RESULT: QUALITY BAR NOT MET")


if __name__ == "__main__":
    run_evaluation()
