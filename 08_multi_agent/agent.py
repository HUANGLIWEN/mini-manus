"""Lesson 08: Multi-Agent - Agent 核心逻辑"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from env import find_and_load_env
from openai_compat import chat_completions, load_config_from_env
from log import init_logger, format_json

from tools.registry import TOOL_REGISTRY as BASE_TOOL_REGISTRY
from tools.search import SearchTool

from multi_agent import AgentSpec, MiniManus as AgentCore, Coordinator


# 创建工具注册表（可复用的基础工具）
BASE_TOOLS = {
    "search": SearchTool(),
}


def create_multi_agent_system(cfg) -> Coordinator:
    """创建多 Agent 系统 - 每个 Agent 都是一个完整的 Agent"""

    # 创建协调器
    coordinator = Coordinator()

    # 创建多个专业 Agent
    # 1. Coder - 编程开发
    coder_spec = AgentSpec(
        name="Coder",
        specialty="编程开发",
        description="专门负责代码编写、调试、优化。给出完整可运行的代码。",
    )
    # Coder 有自己的工具配置，需要传入协调器
    coder_tools = {**BASE_TOOLS, "terminate": BASE_TOOL_REGISTRY.get("terminate")}
    coder = AgentCore(coder_spec, cfg, coder_tools, coordinator)
    coordinator.register(coder)

    # 2. Searcher - 信息搜索
    searcher_spec = AgentSpec(
        name="Searcher",
        specialty="信息搜索",
        description="专门负责搜索信息、查找资料。使用搜索工具获取最新信息。",
    )
    searcher_tools = {**BASE_TOOLS, "terminate": BASE_TOOL_REGISTRY.get("terminate")}
    searcher = AgentCore(searcher_spec, cfg, searcher_tools, coordinator)
    coordinator.register(searcher)

    # 3. Analyzer - 分析总结
    analyzer_spec = AgentSpec(
        name="Analyzer",
        specialty="分析总结",
        description="专门负责分析问题、总结内容、对比差异。给出结构化的分析。",
    )
    analyzer_tools = {**BASE_TOOLS, "terminate": BASE_TOOL_REGISTRY.get("terminate")}
    analyzer = AgentCore(analyzer_spec, cfg, analyzer_tools, coordinator)
    coordinator.register(analyzer)

    return coordinator


@dataclass
class MiniManusAgent:
    """多 Agent 入口 - 外部是单个 Agent，内部是多个 MiniManus"""

    max_steps: int = 10
    log_dir: Path | None = None

    def run(self, *, task: str, session_id: str = "default") -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        # 创建多 Agent 系统（协调器）
        coordinator = create_multi_agent_system(cfg)

        logger.info("=" * 60)
        logger.info("多 Agent 系统初始化")
        logger.info("=" * 60)
        logger.info(f"已注册 Agent: {coordinator.list_agents()}")

        # 使用协调器分发任务
        result = coordinator.dispatch(task)

        logger.info("*" * 60)
        logger.info("* 最终答案")
        logger.info("*" * 60)
        logger.info(result)


# 兼容旧接口
MiniManus = MiniManusAgent
