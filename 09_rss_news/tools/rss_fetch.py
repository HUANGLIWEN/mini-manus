"""RSS Fetch Tool - 获取 RSS 文章"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

import sys

# 添加路径：lib + rss模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rss.parser import RSSParser
from .base import BaseTool


class RSSFetchTool(BaseTool):
    """RSS 解析工具"""

    def __init__(self, opml_path: str):
        self.opml_path = opml_path

    @property
    def name(self) -> str:
        return "rss_fetch"

    @property
    def description(self) -> str:
        return "获取 RSS 订阅源的文章列表"

    def execute(
        self, max_items: int = 20, max_feeds: int = 10, **kwargs
    ) -> tuple[bool, str]:
        parser = RSSParser(self.opml_path, max_feeds=max_feeds)
        parser.load_feeds()
        items = parser.fetch_all()

        # 只返回最新的几篇
        items = items[:max_items]

        result = []
        for item in items:
            result.append(
                {
                    "title": item.title,
                    "link": item.link,
                    "source": item.source,
                    "summary": item.summary[:200] if item.summary else "",
                }
            )

        return True, json.dumps(result, ensure_ascii=False, indent=2)

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_items": {"type": "integer", "description": "最多获取的文章数"}
            },
        }


__all__ = ["RSSFetchTool"]
