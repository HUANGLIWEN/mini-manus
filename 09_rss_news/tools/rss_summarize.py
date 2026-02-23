"""RSS Summarize Tool - 整理文章列表

注意：这个工具只是简单处理，不调用 LLM。
摘要生成由 Summarizer Agent 自己用 LLM 思考完成。
"""

import json
from typing import Any

from .base import BaseTool


class RSSSummarizeTool(BaseTool):
    """简单的摘要处理工具 - 只整理数据，让 Agent 自己生成摘要"""

    @property
    def name(self) -> str:
        return "rss_summarize"

    @property
    def description(self) -> str:
        return "整理文章列表，为后续生成摘要做准备"

    def execute(
        self, articles: str = "", max_articles: int = 5, **kwargs
    ) -> tuple[bool, str]:
        """只是整理文章列表，不做真正的摘要"""
        items = json.loads(articles)
        selected = items[:max_articles]

        # 整理格式，方便 LLM 阅读
        result = []
        for item in selected:
            result.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "source": item.get("source", ""),
                    "original_summary": item.get("summary", ""),
                }
            )

        return True, json.dumps(result, ensure_ascii=False, indent=2)

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "articles": {"type": "string", "description": "JSON 格式的文章列表"},
                "max_articles": {"type": "integer", "description": "最多处理的文章数"},
            },
            "required": ["articles"],
        }


__all__ = ["RSSSummarizeTool"]
