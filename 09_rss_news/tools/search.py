"""Search 工具 - 网页搜索"""

from __future__ import annotations

import json
import os
from typing import Any

from .base import BaseTool


class SearchTool(BaseTool):
    """网页搜索工具，使用 Tavily API"""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search the web for current information. Use this when you need to look up recent events, facts, or any information that may not be in the model's training data."

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        """执行网页搜索"""
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        # 延迟导入，避免启动时就检查 Tavily
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_KEY")
        if not api_key:
            return False, json.dumps({"error": "TAVILY_KEY not found in environment"})

        client = TavilyClient(api_key=api_key)
        results = client.search(query=query, max_results=max_results)

        # 简化返回结果
        simplified = []
        for r in results.get("results", []):
            simplified.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:200],
                }
            )

        return False, json.dumps(simplified, ensure_ascii=False, indent=2)
