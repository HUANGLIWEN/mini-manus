"""Lesson 09: RSS News Agent - 基于 Lesson 08 的 MiniManus"""

import sys
from pathlib import Path

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from loguru import logger

from tools.registry import TOOL_REGISTRY as RSS_TOOL_REGISTRY
from tools.search import SearchTool

from multi_agent import AgentSpec, MiniManus as AgentCore, Coordinator


# 基础工具
BASE_TOOLS = {
    "search": SearchTool(),
}


def create_multi_agent_system(cfg) -> Coordinator:
    """创建多 Agent 系统 - 基于 Lesson 08 架构"""

    coordinator = Coordinator()

    # 合并工具
    all_tools = {**BASE_TOOLS, **RSS_TOOL_REGISTRY}

    # 1. Fetcher - 获取 RSS
    fetcher_spec = AgentSpec(
        name="Fetcher",
        specialty="RSS 获取",
        description="专门负责获取 RSS 订阅源的文章列表",
    )
    fetcher_tools = {**all_tools}
    fetcher = AgentCore(fetcher_spec, cfg, fetcher_tools, coordinator)
    coordinator.register(fetcher)

    # 2. Filter - 内容过滤
    filter_spec = AgentSpec(
        name="Filter",
        specialty="内容过滤",
        description="专门负责过滤 AI/Agent 相关的文章",
    )
    filter_tools = {**all_tools}
    filter_agent = AgentCore(filter_spec, cfg, filter_tools, coordinator)
    coordinator.register(filter_agent)

    # 3. Summarizer - 摘要生成
    summarize_spec = AgentSpec(
        name="Summarizer",
        specialty="摘要生成",
        description="专门负责生成文章摘要",
    )
    summarize_tools = {**all_tools}
    summarize_agent = AgentCore(summarize_spec, cfg, summarize_tools, coordinator)
    coordinator.register(summarize_agent)

    # 4. Reporter - 简报生成
    report_spec = AgentSpec(
        name="Reporter",
        specialty="简报生成",
        description="专门负责生成每日新闻简报",
    )
    report_tools = {**all_tools}
    report_agent = AgentCore(report_spec, cfg, report_tools, coordinator)
    coordinator.register(report_agent)

    return coordinator
