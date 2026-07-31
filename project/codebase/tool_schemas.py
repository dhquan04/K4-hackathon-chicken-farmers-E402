"""Load tool declarations from artifacts/tools.yaml for OpenAI function calling."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import yaml

TOOLS_YAML_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "tools.yaml")


def _clean_schema_node(node: Any) -> Any:
    if isinstance(node, dict):
        cleaned: dict[str, Any] = {}
        for key, value in node.items():
            if key == "default" and value is None:
                continue
            cleaned[key] = _clean_schema_node(value)
        return cleaned
    if isinstance(node, list):
        return [_clean_schema_node(item) for item in node]
    return node


def _to_openai_tool(entry: dict[str, Any]) -> dict[str, Any]:
    params = _clean_schema_node(entry.get("parameters") or {"type": "object", "properties": {}})
    description = entry.get("description", "")
    if isinstance(description, str):
        description = " ".join(description.split())
    return {
        "type": "function",
        "function": {
            "name": entry["name"],
            "description": description,
            "parameters": params,
        },
    }


@lru_cache(maxsize=1)
def load_openai_tools() -> list[dict[str, Any]]:
    with open(TOOLS_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [_to_openai_tool(entry) for entry in data.get("tools", [])]
