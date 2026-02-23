"""RSS Filter Tool - 过滤相关文章

注意：不过滤，由 Agent 自己判断是否相关。
"""

import json
from typing import Any

from .base import BaseTool


class RSSFilterTool(BaseTool):
    """内容过滤工具 - 让 Agent 自己判断是否相关"""

    @property
    def name(self) -> str:
        return "rss_filter"

    @property
    def description(self) -> str:
        return "获取需要筛选的文章列表，由 Agent 判断是否相关"

    def execute(self, articles: str = "", **kwargs) -> tuple[bool, str]:
        """直接返回文章列表，让 Agent 自己判断"""
        # 直接返回，不做过滤
        return True, articles

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "articles": {"type": "string", "description": "JSON 格式的文章列表"},
            },
            "required": ["articles"],
        }


__all__ = ["RSSFilterTool"]
