"""RSS Report Tool - 生成每日简报"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import BaseTool


class RSSReportTool(BaseTool):
    """简报生成工具"""

    @property
    def name(self) -> str:
        return "rss_report"

    @property
    def description(self) -> str:
        return "生成每日新闻简报"

    def execute(
        self, summaries: str = "", output_path: str = "", **kwargs
    ) -> tuple[bool, str]:
        summaries_data = json.loads(summaries)
        date = datetime.now().strftime("%Y年%m月%d日")

        report = f"""# 📰 AI Agent 每日简报

**日期**: {date}

---

"""

        for i, item in enumerate(summaries_data, 1):
            report += f"""### {i}. {item["title"]}

**来源**: {item["source"]}

{item["summary"]}

[原文链接]({item["link"]})

---

"""

        report += """## 📮 订阅说明

- RSS 源来自 HN 2025 最热门博客
- 每天自动抓取并筛选 AI/Agent 相关内容
- 由 MiniManus Agent 自动生成

---
*由 AI Agent 自动生成*
"""

        # 如果指定了输出路径，写入文件
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(exist_ok=True)
            output_file.write_text(report, encoding="utf-8")
            return True, f"简报已保存到: {output_path}\n\n{report}"

        return True, report

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summaries": {"type": "string", "description": "JSON 格式的摘要列表"},
                "output_path": {
                    "type": "string",
                    "description": "输出文件路径（可选）",
                },
            },
            "required": ["summaries"],
        }


__all__ = ["RSSReportTool"]
