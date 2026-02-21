"""Lesson 07: Multi-turn Conversation - Agent 核心逻辑"""

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
from message import MessageStore
from message.compression import (
    should_compress,
    compress_conversation,
    estimate_tokens,
)


# 添加搜索工具到注册表
_search = SearchTool()

TOOL_REGISTRY = {**BASE_TOOL_REGISTRY, "search": _search}


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """执行工具"""
    tool = TOOL_REGISTRY.get(name)
    if tool:
        return tool.execute(**arguments)
    raise RuntimeError(f"Unknown tool: {name}")


@dataclass
class SessionManager:
    """会话管理器"""

    message_store: MessageStore

    def create_or_get(self, session_id: str) -> str:
        """创建或获取会话"""
        count = self.message_store.count(session_id)
        if count == 0:
            logger.info(f"[会话] 创建新会话: {session_id}")
        else:
            logger.info(f"[会话] 恢复会话: {session_id} ({count} 条消息)")
        return session_id

    def list_sessions(self) -> list[dict]:
        """列出所有会话"""
        return self.message_store.list_sessions()

    def get_history(self, session_id: str, limit: int = 20) -> list[dict]:
        """获取会话历史"""
        return self.message_store.get_recent(limit=limit, session_id=session_id)


@dataclass
class MiniManus:
    """支持多轮对话的 Agent"""

    max_steps: int = 10
    log_dir: Path | None = None
    max_tokens: int = 4000

    def _system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in TOOL_REGISTRY.items():
            tool_descriptions.append(f"- `{tool.name}` - {tool.description}")

        tools_list = "\n".join(tool_descriptions)

        return (
            "You are MiniManus, an AI Agent with multi-turn conversation support.\n\n"
            f"You have access to these tools:\n{tools_list}\n\n"
            "The conversation history is stored in SQLite, organized by session_id.\n"
            "When you have the final answer, call `terminate`.\n"
        )

    def run(self, *, task: str, session_id: str = "default") -> None:
        """
        运行 Agent（单任务模式）

        Args:
            task: 用户任务
            session_id: 会话 ID
        """
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        # 初始化消息存储
        db_path = Path(__file__).parent / "message" / "messages.db"
        message_store = MessageStore(str(db_path))

        # 会话管理
        session_mgr = SessionManager(message_store)
        session_id = session_mgr.create_or_get(session_id)

        tools = [tool.schema() for tool in TOOL_REGISTRY.values()]

        # 获取历史消息
        history = message_store.get_recent(limit=20, session_id=session_id)

        logger.info("=" * 60)
        logger.info("Step 0: 初始上下文")
        logger.info("=" * 60)

        # 计算并显示 token 估算
        total_tokens = sum(estimate_tokens(m.get("content", "")) for m in history)
        logger.info(f"会话: {session_id}")
        logger.info(f"历史消息数量: {len(history)} 条")
        logger.info(f"估算 token 数量: {total_tokens} (阈值: {self.max_tokens})")

        # 检查是否需要压缩
        if should_compress(history, self.max_tokens):
            logger.info(
                f"[压缩] 需要压缩！当前 {total_tokens} tokens > {self.max_tokens} tokens"
            )
            logger.info(f"[压缩] 正在压缩 {len(history)} 条消息...")

            compressed = compress_conversation(history, cfg)

            new_tokens = sum(estimate_tokens(m.get("content", "")) for m in compressed)
            logger.info(
                f"[压缩] 压缩完成！{total_tokens} tokens -> {new_tokens} tokens (节省 {total_tokens - new_tokens} tokens)"
            )
            logger.info(f"[压缩] 消息数量: {len(history)} 条 -> {len(compressed)} 条")

            history = compressed
        else:
            logger.info(
                f"[无需压缩] 当前 {total_tokens} tokens <= {self.max_tokens} tokens"
            )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            *history,
            {"role": "user", "content": task},
        ]

        logger.info(format_json(messages))
        logger.info(f"\nAvailable tools: {len(tools)}")
        logger.info(f"Tools: {[t['function']['name'] for t in tools]}")

        for step in range(1, self.max_steps + 1):
            logger.info("#" * 60)
            logger.info(f"# Step {step}")
            logger.info("#" * 60)

            resp = chat_completions(
                cfg=cfg, messages=messages, tools=tools, tool_choice="auto"
            )

            logger.info(f"Step {step}: LLM response")
            logger.info(format_json(resp))

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if tool_calls:
                for idx, call in enumerate(tool_calls):
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""

                    raw_args = fn.get("arguments") or "{}"

                    try:
                        args = (
                            json.loads(raw_args)
                            if isinstance(raw_args, str)
                            else dict(raw_args)
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Invalid tool arguments for {name}: {raw_args}"
                        ) from e

                    logger.info(f"Step {step}: Calling tool {name}")
                    logger.info(format_json({"arguments": args}))

                    should_stop, output = execute_tool(name, args)

                    logger.info(f"Step {step}: Tool returned")
                    logger.info(output[:500] + "..." if len(output) > 500 else output)

                    tool_result_msg = (
                        f"[TOOL_CALL {name}] {json.dumps(args)}\n[TOOL_RESULT] {output}"
                    )
                    messages.append({"role": "user", "content": tool_result_msg})

                    if should_stop:
                        logger.info("*" * 60)
                        logger.info("* Final Answer (Agent Loop Terminated)")
                        logger.info("*" * 60)
                        logger.info(output)

                        # 存储最终消息
                        message_store.add("user", task, session_id)
                        message_store.add("assistant", output, session_id)

                        # 显示当前会话消息统计
                        total_msgs = message_store.count(session_id)
                        logger.info(f"[消息] 共存储 {total_msgs} 条消息")
                        return

                logger.info(f"Step {step}: Updated messages")
                logger.info(format_json(messages))
                continue

            if content:
                logger.info("*" * 60)
                logger.info("* LLM returned content directly (no tool call)")
                logger.info("*" * 60)
                logger.info(content)

                # 存储消息
                message_store.add("user", task, session_id)
                message_store.add("assistant", content, session_id)

                # 显示当前会话消息统计
                total_msgs = message_store.count(session_id)
                logger.info(f"[消息] 共存储 {total_msgs} 条消息")
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )
