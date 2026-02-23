"""Terminate 工具 - 终止 Agent Loop"""

from __future__ import annotations

from typing import Any

from .base import BaseTool


class TerminateTool(BaseTool):
    """终止 Agent Loop，返回最终答案"""

    @property
    def name(self) -> str:
        return "terminate"

    @property
    def description(self) -> str:
        return """终止 Agent Loop。

当任务已完成时调用此工具，将最终答案返回给用户。
传入 'final' 参数作为最终答案。"""

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "final": {
                    "type": "string",
                    "description": "最终答案",
                },
            },
            "required": ["final"],
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        final = kwargs.get("final", "")
        return True, final
