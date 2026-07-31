"""
FoodFlow AI Agent — OpenAI tool calling + natural-language answer generation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from project.codebase.tool_schemas import load_openai_tools
from project.codebase.workflow import (
    OUT_OF_SCOPE_MESSAGE,
    detect_intent,
    handle_message,
    run_tool_for_agent,
)
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

try:
    from project.codebase.workflow import handle_message, detect_intent
except ImportError:
    from workflow import handle_message, detect_intent

PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "prompts.md")
_CODEBASE_DIR = os.path.dirname(__file__)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = os.path.join(_CODEBASE_DIR, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    if not os.environ.get("OPENAI_API_KEY") and os.environ.get("API_KEY_ORDER"):
        os.environ["OPENAI_API_KEY"] = os.environ["API_KEY_ORDER"]


_load_env()


def load_system_prompt() -> str:
    if os.path.exists(PROMPT_FILE_PATH):
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return (
        "Bạn là FoodFlow, trợ lý AI hỗ trợ đặt món ăn bằng tiếng Việt tại Vinhomes Ocean Park & Hà Nội. "
        "Chỉ hỗ trợ: Tìm món, Xem menu, Quản lý giỏ hàng, Tính tiền, Tạo đơn, Theo dõi đơn. "
        "Trả lời thân thiện, lịch sự và ngắn gọn."
    )


MAX_MENU_ITEMS_FOR_LLM = 12


def _compact_tool_result(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    """Shrink large tool payloads so the answer-generation LLM call fits context."""
    data = result.get("data") or {}
    compact: dict[str, Any] = {
        "ok": result.get("ok"),
        "message": result.get("message"),
        "needs_confirmation": result.get("needs_confirmation"),
    }

    if tool_name in ("get_menu", "search_food"):
        items = data.get("items") or data.get("results") or []
        compact["total_items"] = len(items)
        compact["items"] = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "price_formatted": item.get("price_formatted") or item.get("price"),
            }
            for item in items[:MAX_MENU_ITEMS_FOR_LLM]
        ]
        if len(items) > MAX_MENU_ITEMS_FOR_LLM:
            compact["truncated"] = True
            compact["note"] = (
                f"Chỉ gửi {MAX_MENU_ITEMS_FOR_LLM}/{len(items)} món đầu. "
                "Gợi ý user lọc theo danh mục hoặc từ khóa nếu cần chi tiết hơn."
            )
        if data.get("available_categories"):
            compact["available_categories"] = data["available_categories"]
        if data.get("category_filter"):
            compact["category_filter"] = data["category_filter"]
        if data.get("query"):
            compact["query"] = data["query"]
        return compact

    compact["data"] = data
    return compact


def _json_tool_payload(tool_name: str, result: dict[str, Any]) -> str:
    payload = _compact_tool_result(tool_name, result)
    return json.dumps(payload, ensure_ascii=False, default=str)


def _merge_tool_kwargs(
    llm_args: dict[str, Any],
    tool_kwargs: Optional[Dict[str, Any]],
) -> dict[str, Any]:
    merged = dict(llm_args or {})
    if tool_kwargs:
        for key, value in tool_kwargs.items():
            if key == "session_id":
                continue
            if value is not None and value != "":
                merged[key] = value
    return merged


class FoodOrderingAgent:
    """LLM chọn tool từ tools.yaml, gọi workflow, rồi generate câu trả lời."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        # gpt-4o-mini (chữ o) — KHÔNG phải gpt-4.0-mini
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.system_prompt = load_system_prompt()
        self.tools = load_openai_tools()

    def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        tool_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sid = session_id or user_id

        if not self.api_key:
            return self._fallback_process(
                user_id=user_id, message=message, session_id=sid, tool_kwargs=tool_kwargs
            )

        if not isinstance(message, str) or not message.strip():
            return {
                "ok": False,
                "tool": None,
                "message": "Bạn muốn đặt món hoặc xem menu?",
                "ai_response": "Bạn muốn đặt món hoặc xem menu?",
            }

        try:
            return self._process_with_llm(message, sid, tool_kwargs)
        except Exception as error:
            res = self._fallback_process(
                user_id=user_id, message=message, session_id=sid, tool_kwargs=tool_kwargs
            )
            res["notice"] = f"Processed via fallback workflow engine ({error})"
            return res

    def _process_with_llm(
        self,
        message: str,
        session_id: str,
        tool_kwargs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        import openai

        client = openai.OpenAI(api_key=self.api_key)
        messages: List[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]

        first = client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=0.2,
        )
        assistant = first.choices[0].message

        if not assistant.tool_calls:
            text = (assistant.content or OUT_OF_SCOPE_MESSAGE).strip()
            inferred = detect_intent(message)

            if inferred:
                probe = handle_message(
                    session_id,
                    message,
                    tool_kwargs=_merge_tool_kwargs({}, tool_kwargs),
                )
                response = {
                    "ok": probe.get("ok", False),
                    "tool": probe.get("tool") or inferred,
                    "message": probe.get("message", text),
                    "ai_response": text,
                    "data": probe.get("data"),
                }
                if probe.get("needs_confirmation"):
                    response["needs_confirmation"] = True
                return response

            return {
                "ok": False,
                "tool": None,
                "message": text,
                "ai_response": text,
            }

        messages.append(
            {
                "role": "assistant",
                "content": assistant.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in assistant.tool_calls
                ],
            }
        )

        primary_tool: Optional[str] = None
        primary_result: Optional[dict[str, Any]] = None
        needs_confirmation = False

        for call in assistant.tool_calls:
            name = call.function.name
            raw_args = call.function.arguments or "{}"
            llm_args = json.loads(raw_args) if raw_args.strip() else {}
            args = _merge_tool_kwargs(llm_args, tool_kwargs)

            result = run_tool_for_agent(name, session_id, args)
            if primary_tool is None:
                primary_tool = name
                primary_result = result
            if result.get("needs_confirmation"):
                needs_confirmation = True

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": _json_tool_payload(name, result),
                }
            )

        try:
            final = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
            )
            ai_text = (final.choices[0].message.content or "").strip()
        except Exception:
            ai_text = primary_result.get("message", "") if primary_result else ""
        if not ai_text and primary_result:
            ai_text = primary_result.get("message", "")

        assert primary_result is not None
        response: Dict[str, Any] = {
            "ok": primary_result.get("ok", False),
            "tool": primary_tool,
            "message": primary_result.get("message", ai_text),
            "ai_response": ai_text or primary_result.get("message", ""),
            "data": primary_result.get("data"),
        }
        if needs_confirmation:
            response["needs_confirmation"] = True
        return response

    def _fallback_process(
        self,
        user_id: str,
        message: str,
        session_id: str,
        tool_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        kwargs = dict(tool_kwargs or {})
        kwargs["session_id"] = session_id
        return handle_message(user_id=user_id, message=message, tool_kwargs=kwargs)
    def process_message(self, user_id: str, message: str, session_id: Optional[str] = None, tool_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message via Workflow dispatcher and OpenAI LLM synthesis.
        """
        sid = session_id or user_id
        kwargs = dict(tool_kwargs or {})
        if "session_id" not in kwargs:
            kwargs["session_id"] = sid
        
        # Dispatch workflow tools first to fetch accurate data
        res = handle_message(user_id=user_id, message=message, tool_kwargs=kwargs)

        # If OpenAI API Key is present, enhance response with OpenAI LLM
        current_key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
        if current_key:
            try:
                import openai
                client = openai.OpenAI(api_key=current_key)
                
                # Context payload from workflow tool execution
                context_str = json.dumps(res, ensure_ascii=False)
                
                prompt_messages = [
                    {
                        "role": "system", 
                        "content": self.system_prompt + "\n\nHãy tổng hợp câu trả lời tự nhiên, tư vấn chu đáo cho khách hàng dựa trên dữ liệu hệ thống dưới đây."
                    },
                    {
                        "role": "user", 
                        "content": f"Câu hỏi của người dùng: '{message}'\n\nDữ liệu từ hệ thống:\n{context_str}"
                    }
                ]
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=prompt_messages,
                    temperature=0.3,
                    max_tokens=450
                )
                
                ai_text = response.choices[0].message.content or ""
                if ai_text:
                    res["ai_response"] = ai_text
                    res["llm_engine"] = f"OpenAI Live ({self.model})"
            except Exception as e:
                res["notice"] = f"Processed via fallback workflow engine ({str(e)})"

        if "ai_response" not in res or not res["ai_response"]:
            res["ai_response"] = res.get("message", "Đã xử lý yêu cầu.")
            res["llm_engine"] = "Rule Workflow Engine"

        return res


def run_agent(
    user_id: str,
    message: str,
    session_id: Optional[str] = None,
    tool_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    agent = FoodOrderingAgent()
    return agent.process_message(
        user_id=user_id,
        message=message,
        session_id=session_id,
        tool_kwargs=tool_kwargs,
    )
