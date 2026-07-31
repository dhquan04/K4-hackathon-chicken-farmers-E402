"""
FoodFlow Eval Runner — MVP Hypothesis Testing

Three test layers:
  - Smoke (--smoke): critical path, must pass 100%
  - Quantitative (--quantitative): golden set intent + workflow assertions
  - Qualitative (--qualitative): print instructions for human scenarios

Usage:
  python eval/run_eval.py --smoke
  python eval/run_eval.py --quantitative
  python eval/run_eval.py --all --run-id 001
  python eval/run_eval.py --all --llm --no-report          # qua agent + OpenAI
  python eval/run_eval.py --smoke --llm --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from project.codebase.workflow import detect_intent, handle_message  # noqa: E402

if TYPE_CHECKING:
    from project.codebase.agent import FoodOrderingAgent

EVAL_DIR = os.path.dirname(__file__)
RUNS_DIR = os.path.join(EVAL_DIR, "runs")
ENV_PATH = os.path.join(ROOT, "project", "codebase", ".env")

SMOKE_BAR = 100.0
QUANT_INTENT_BAR = 80.0


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    if os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH)
    if not os.environ.get("OPENAI_API_KEY") and os.environ.get("API_KEY_ORDER"):
        os.environ["OPENAI_API_KEY"] = os.environ["API_KEY_ORDER"]


def load_json(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def expected_tools(case: dict[str, Any]) -> list[str | None]:
    if "expected_tools" in case:
        return case["expected_tools"]
    return [case.get("expected_tool")]


def intent_pass(case: dict[str, Any], detected: str | None) -> bool:
    return detected in expected_tools(case)


def check_workflow_assertion(result: dict[str, Any], assertion: str) -> bool:
    ok = result.get("ok", False)
    tool = result.get("tool")
    message = (result.get("message") or "").lower()

    if assertion == "out_of_scope":
        return not ok and tool is None
    if assertion == "needs_confirmation":
        return result.get("needs_confirmation") is True
    if assertion == "not_needs_confirmation":
        return not result.get("needs_confirmation")
    if assertion == "not_ok":
        return not ok
    if assertion == "not_ok_missing_param":
        return not ok and ("vui lòng cung cấp" in message or "cung cấp" in message)
    if assertion == "empty_input":
        return not ok and tool is None and "đặt món" in message
    if assertion == "not_ok_or_out_of_scope":
        return (not ok and tool is None) or (not ok)
    if assertion == "out_of_scope_or_not_ok":
        return (not ok and tool is None) or not ok
    if assertion == "not_ok_or_empty":
        return not ok
    if assertion == "track_not_found":
        data = result.get("data") or {}
        msg = (data.get("message") or result.get("message") or "").lower()
        return data.get("status") == "warning" and "không tìm thấy" in msg
    if assertion == "search_not_found":
        data = result.get("data") or {}
        return data.get("status") == "warning" or not (data.get("results") or [])
    return ok


def evaluate_case(
    case: dict[str, Any],
    *,
    check_workflow: bool,
    use_llm: bool = False,
    agent: FoodOrderingAgent | None = None,
) -> dict[str, Any]:
    user_input = case.get("input", "")
    session = f"eval_{case.get('id', 'x')}"
    kwargs = dict(case.get("tool_kwargs") or {})
    assertion = case.get("workflow_assertion")

    workflow_ok: bool | None = None
    workflow_result: dict[str, Any] | None = None
    llm_fallback = False
    detected: str | None = None

    if use_llm and agent is not None:
        workflow_result = agent.process_message(
            session,
            user_input,
            session_id=session,
            tool_kwargs=kwargs,
        )
        detected = workflow_result.get("tool")
        llm_fallback = bool(workflow_result.get("notice"))
        if check_workflow and assertion:
            workflow_ok = check_workflow_assertion(workflow_result, assertion)
    else:
        detected = detect_intent(user_input) if user_input.strip() else None
        if check_workflow and assertion:
            workflow_result = handle_message(session, user_input, tool_kwargs=kwargs)
            workflow_ok = check_workflow_assertion(workflow_result, assertion)

    intent_ok = intent_pass(case, detected)

    overall = intent_ok
    if workflow_ok is not None:
        overall = intent_ok and workflow_ok

    output_message = None
    if workflow_result:
        output_message = workflow_result.get("ai_response") or workflow_result.get("message")

    return {
        "id": case.get("id"),
        "description": case.get("description", ""),
        "hypothesis": case.get("hypothesis"),
        "layer": case.get("layer"),
        "source": case.get("source"),
        "input": user_input,
        "expected_response": case.get("expected_response", ""),
        "expected": expected_tools(case),
        "detected": detected,
        "output": output_message,
        "intent_ok": intent_ok,
        "workflow_assertion": assertion,
        "workflow_ok": workflow_ok,
        "pass": overall if workflow_ok is not None else intent_ok,
        "workflow_result": workflow_result,
        "llm_fallback": llm_fallback,
    }


def run_suite(
    cases: list[dict[str, Any]],
    *,
    suite_name: str,
    check_workflow: bool,
    pass_bar: float,
    use_llm: bool = False,
    agent: FoodOrderingAgent | None = None,
) -> dict[str, Any]:
    results = [
        evaluate_case(c, check_workflow=check_workflow, use_llm=use_llm, agent=agent)
        for c in cases
    ]
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    rate = (passed / total * 100) if total else 0.0

    intent_passed = sum(1 for r in results if r["intent_ok"])
    intent_rate = (intent_passed / total * 100) if total else 0.0

    workflow_cases = [r for r in results if r["workflow_assertion"]]
    workflow_passed = sum(1 for r in workflow_cases if r["workflow_ok"])
    workflow_rate = (
        (workflow_passed / len(workflow_cases) * 100) if workflow_cases else None
    )

    bar_met = rate >= pass_bar

    print(f"\n=== {suite_name.upper()} ({total} cases) ===")
    for r in results:
        status = "[PASS]" if r["pass"] else "[FAIL]"
        print(f"{status} {r['id']}: {r['description']}")
        print(f"   Input: '{r['input']}'")
        print(f"   Expected: {r['expected']} | Detected: {r['detected']}")
        if r["workflow_assertion"]:
            wf = "PASS" if r["workflow_ok"] else "FAIL"
            print(f"   Workflow ({r['workflow_assertion']}): {wf}")
        if use_llm and r.get("llm_fallback"):
            print("   LLM: fallback (API lỗi hoặc thiếu key)")
        elif use_llm and r.get("output"):
            print(f"   LLM output: {truncate(r.get('output'), 80)}")
        print()

    print(f"--- {suite_name} summary ---")
    print(f"Overall pass: {passed}/{total} ({rate:.1f}%)")
    print(f"Intent pass:  {intent_passed}/{total} ({intent_rate:.1f}%)")
    if workflow_rate is not None:
        print(f"Workflow pass: {workflow_passed}/{len(workflow_cases)} ({workflow_rate:.1f}%)")
    print(f"Bar ({pass_bar:.0f}%): {'MET' if bar_met else 'NOT MET'}")
    print()

    return {
        "suite": suite_name,
        "total": total,
        "passed": passed,
        "rate": round(rate, 1),
        "intent_rate": round(intent_rate, 1),
        "workflow_rate": round(workflow_rate, 1) if workflow_rate is not None else None,
        "bar": pass_bar,
        "bar_met": bar_met,
        "results": results,
    }


def print_qualitative_info() -> None:
    print("\n=== QUALITATIVE TEST (manual) ===")
    print("Chạy 6 scenario trong eval/qualitative/scenarios.md")
    print("Chấm bằng eval/qualitative/scorecard_template.md")
    print("Quality bar: ≥4/6 scenario pass cả 4 chiều (D1–D4)")
    print("Hai người chấm độc lập scenario Q-03 và Q-04, so kết quả.\n")


REAL_WORLD_SOURCES = {"self-test", "chatlog-derived", "survey", "discord"}


def cp3_stats(cases: list[dict[str, Any]]) -> dict[str, Any]:
    layer_counts = {"1": 0, "2": 0, "3": 0, "4": 0}
    real_world = 0
    for c in cases:
        layer = str(c.get("layer", ""))
        if layer in layer_counts:
            layer_counts[layer] += 1
        if c.get("source") in REAL_WORLD_SOURCES:
            real_world += 1
    return {
        "total": len(cases),
        "layer_counts": layer_counts,
        "real_world": real_world,
    }


def truncate(text: str | None, limit: int = 48) -> str:
    if not text:
        return ""
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def write_report(run_id: str, summaries: list[dict[str, Any]], *, use_llm: bool = False) -> str:
    os.makedirs(RUNS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    golden_path = os.path.join(EVAL_DIR, "golden_set.json")
    golden_cases = load_json(golden_path) if os.path.exists(golden_path) else []
    stats = cp3_stats(golden_cases)

    payload = {
        "run_id": run_id,
        "timestamp": ts,
        "mode": "llm" if use_llm else "workflow",
        "cp3": stats,
        "suites": summaries,
    }
    json_path = os.path.join(RUNS_DIR, f"run-{run_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    quant = next((s for s in summaries if s["suite"] == "quantitative"), None)
    cp3_score = (
        f"{quant['passed']}/{quant['total']}" if quant else "—"
    )

    md_path = os.path.join(RUNS_DIR, f"run-{run_id}.md")
    lines = [
        f"# Eval Run {run_id}",
        f"",
        f"**Timestamp (UTC):** {ts}",
        f"**Mode:** {'LLM (run_agent)' if use_llm else 'workflow rule-based'}",
        f"",
        f"## CP3 form (golden set)",
        f"",
        f"| Mục form | Giá trị |",
        f"|---|---|",
        f"| Tổng câu thử | {stats['total']} |",
        f"| Lớp ① không bịa | {stats['layer_counts']['1']} (cần ≥2) |",
        f"| Lớp ② mơ hồ | {stats['layer_counts']['2']} (cần ≥2) |",
        f"| Lớp ③ ngoài phạm vi | {stats['layer_counts']['3']} (cần ≥2) |",
        f"| Lớp ④ hậu quả domain | {stats['layer_counts']['4']} (cần ≥2) |",
        f"| Câu từ quan sát thực tế | {stats['real_world']} (cần ≥5) |",
        f"| **Kết quả lần chạy đầu** | **{cp3_score}** |",
        f"",
        f"## Quality bar (spec.md §7 / mvp_hypotheses.md)",
        f"",
        f"- Smoke: 100%",
        f"- Quantitative: ≥80% pass trên golden set",
        f"- Điều kiện cứng: 0 case fail D1 (không bịa dữ liệu nghiệp vụ)",
        f"- Qualitative: ≥4/6 scenarios (manual — xem scorecard)",
        f"",
        f"## Summary",
        f"",
        f"| Suite | Pass | Rate | Bar | Met? |",
        f"|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['suite']} | {s['passed']}/{s['total']} | {s['rate']}% | {s['bar']:.0f}% | {'✓' if s['bar_met'] else '✗'} |"
        )

    if quant:
        lines.extend(
            [
                "",
                "## Golden set — bảng kết quả đầy đủ (CP3 câu 5)",
                "",
                "| ID | Layer | Pass | Input | Expected response | Output (rút gọn) |",
                "|---|---|---|---|---|---|",
            ]
        )
        for r in quant["results"]:
            status = "✓" if r["pass"] else "✗"
            lines.append(
                f"| {r['id']} | {r.get('layer', '')} | {status} | "
                f"{truncate(r['input'], 36)} | {truncate(r.get('expected_response'), 40)} | "
                f"{truncate(r.get('output'), 36)} |"
            )

    lines.extend(["", "## Failed cases (tóm tắt)", ""])
    for s in summaries:
        fails = [r for r in s["results"] if not r["pass"]]
        if not fails:
            lines.append(f"### {s['suite']}: none")
            continue
        lines.append(f"### {s['suite']}")
        lines.append("")
        lines.append("| ID | Input | Expected | Detected | Note |")
        lines.append("|---|---|---|---|---|")
        for r in fails:
            note = r.get("workflow_assertion") or ""
            lines.append(
                f"| {r['id']} | {truncate(r['input'], 40)} | {r['expected']} | {r['detected']} | {note} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Next steps",
            "",
            "1. Chọn failure đau nhất → sửa prompt/workflow",
            "2. Chạy qualitative scenarios nếu chưa có scorecard",
            "3. `python eval/run_eval.py --all --run-id NNN` chạy lại trọn bộ",
            "",
        ]
    )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written: {md_path}")
    print(f"JSON report:    {json_path}")
    if quant:
        print(f"CP3 golden set score: {cp3_score}")
    return md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="FoodFlow MVP eval runner")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--quantitative", action="store_true", help="Run golden set")
    parser.add_argument("--qualitative", action="store_true", help="Show qualitative instructions")
    parser.add_argument("--all", action="store_true", help="Smoke + quantitative")
    parser.add_argument("--run-id", default="001", help="Run id for reports (default: 001)")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Chạy qua FoodOrderingAgent + OpenAI (cần OPENAI_API_KEY trong .env)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model khi dùng --llm (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Không ghi file runs/run-*.md và .json",
    )
    args = parser.parse_args()

    load_env()

    if not any([args.smoke, args.quantitative, args.qualitative, args.all]):
        args.all = True

    agent: FoodOrderingAgent | None = None
    if args.llm:
        from project.codebase.agent import FoodOrderingAgent

        agent = FoodOrderingAgent(model=args.model)
        if not agent.api_key:
            print(
                "ERROR: --llm cần OPENAI_API_KEY (hoặc API_KEY_ORDER) "
                f"trong {ENV_PATH} hoặc biến môi trường."
            )
            sys.exit(1)
        print(f"\n=== LLM MODE ===")
        print(f"Model: {args.model}")
        print(f"Env:   {ENV_PATH if os.path.exists(ENV_PATH) else 'biến môi trường'}")
        print()

    summaries: list[dict[str, Any]] = []

    if args.qualitative:
        print_qualitative_info()
        if not (args.smoke or args.quantitative or args.all):
            return

    if args.smoke or args.all:
        smoke = load_json(os.path.join(EVAL_DIR, "smoke_tests.json"))
        summaries.append(
            run_suite(
                smoke,
                suite_name="smoke",
                check_workflow=True,
                pass_bar=SMOKE_BAR,
                use_llm=args.llm,
                agent=agent,
            )
        )

    if args.quantitative or args.all:
        golden = load_json(os.path.join(EVAL_DIR, "golden_set.json"))
        summaries.append(
            run_suite(
                golden,
                suite_name="quantitative",
                check_workflow=True,
                pass_bar=QUANT_INTENT_BAR,
                use_llm=args.llm,
                agent=agent,
            )
        )

    if summaries and (args.all or args.smoke or args.quantitative) and not args.no_report:
        write_report(args.run_id, summaries, use_llm=args.llm)

    if args.all:
        print_qualitative_info()


if __name__ == "__main__":
    main()
