"""工具注册表"""

from pathlib import Path
from .base import BaseTool
from .rss_fetch import RSSFetchTool
from .rss_filter import RSSFilterTool
from .rss_summarize import RSSSummarizeTool
from .rss_report import RSSReportTool

# OPML 路径
OPML_PATH = str(
    Path(__file__).resolve().parent.parent.parent
    / ".."
    / "news"
    / "hn-popular-blogs-2025.opml"
)

# 创建工具实例
_rss_fetch = RSSFetchTool(OPML_PATH)
_rss_filter = RSSFilterTool()
_rss_summarize = RSSSummarizeTool()
_rss_report = RSSReportTool()

# 注册表
TOOL_REGISTRY: dict[str, BaseTool] = {
    "rss_fetch": _rss_fetch,
    "rss_filter": _rss_filter,
    "rss_summarize": _rss_summarize,
    "rss_report": _rss_report,
}
