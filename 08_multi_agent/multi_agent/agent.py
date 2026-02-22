"""Multi-Agent 模块 - Agent 实现"""

from dataclasses import dataclass, field
from typing import Optional
from loguru import logger

import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))

from openai_compat import chat_completions, load_config_from_env


@dataclass
class AgentSpec:
    """Agent 规格定义"""

    name: str
    specialty: str  # 专业领域
    description: str
    tools: list = field(default_factory=list)  # 工具列表


class MiniManus:
    """MiniManus Agent - 每个 Agent 都是一个完整的 MiniManus"""

    def __init__(
        self, spec: AgentSpec, cfg, tools_registry: dict, coordinator: "Coordinator"
    ):
        self.spec = spec
        self.cfg = cfg
        self.tools_registry = tools_registry
        self.coordinator = coordinator  # 只能通过协调器与其他 Agent 通讯
        self.max_steps = 10

    @property
    def name(self) -> str:
        return self.spec.name

    def run(self, task: str, context: list[dict] | None = None) -> str:
        """执行任务"""

        logger.info(f"[{self.spec.name}] 开始处理任务: {task[:50]}...")

        # 构建消息
        messages = self._build_messages(task, context)

        # 获取工具 schema
        tools = [tool.schema() for tool in self.tools_registry.values()]

        # Agent Loop
        for step in range(1, self.max_steps + 1):
            resp = chat_completions(
                cfg=self.cfg,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto",
            )

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if tool_calls:
                for call in tool_calls:
                    fn = call.get("function") or {}
                    name = fn.get("name", "")
                    raw_args = fn.get("arguments", "{}")

                    try:
                        args = (
                            json.loads(raw_args)
                            if isinstance(raw_args, str)
                            else dict(raw_args)
                        )
                    except:
                        args = {}

                    # 检查是否是请求协调器（唯一允许的跨 Agent 通讯方式）
                    if name == "request_help":
                        # 请求协调器转交给其他 Agent
                        target_agent = args.get("agent", "")
                        task_desc = args.get("task", "")
                        logger.info(
                            f"[{self.spec.name}] 请求协调器转交给 {target_agent}"
                        )

                        # 通过协调器执行子任务
                        result = self.coordinator.handoff(
                            from_agent=self.name,
                            to_agent=target_agent,
                            task=task_desc,
                            context=messages,
                        )

                        # 将结果添加到上下文
                        messages.append(
                            {"role": "user", "content": f"[协调器返回]: {result}"}
                        )
                        continue

                    # 执行普通工具
                    tool = self.tools_registry.get(name)
                    if tool:
                        should_stop, output = tool.execute(**args)
                    else:
                        output = f"Unknown tool: {name}"
                        should_stop = False

                    tool_result = (
                        f"[TOOL_CALL {name}] {json.dumps(args)}\n[TOOL_RESULT] {output}"
                    )
                    messages.append({"role": "user", "content": tool_result})

                    if should_stop:
                        logger.info(f"[{self.spec.name}] 任务完成")
                        return output

                continue

            if content:
                logger.info(f"[{self.spec.name}] 任务完成")
                return content

        return "任务超时"

    def _build_messages(
        self, task: str, context: list[dict] | None = None
    ) -> list[dict]:
        """构建消息列表"""
        messages = [{"role": "system", "content": self._system_prompt()}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": task})
        return messages

    def _system_prompt(self) -> str:
        return f"""你是 {self.spec.name}，专门负责 {self.spec.specialty}。

{self.spec.description}

重要：当你需要其他 Agent 帮助时，只能使用 request_help 工具请求协调器转交任务。
不要尝试直接调用其他 Agent。

当任务完成时，直接给出最终答案。"""


class Coordinator:
    """协调器 - 多 Agent 系统的中心 Hub，所有跨 Agent 通讯必须经过这里"""

    def __init__(self):
        self.agents: dict[str, MiniManus] = {}
        self.task_history: list[dict] = []  # 任务历史
        self.cfg = load_config_from_env()

    def register(self, agent: MiniManus):
        """注册 Agent"""
        self.agents[agent.name] = agent
        logger.info(f"[Coordinator] 注册 Agent: {agent.name} ({agent.spec.specialty})")

    def dispatch(self, task: str) -> str:
        """分发主任务 - 入口"""

        logger.info(f"[Coordinator] 收到主任务: {task[:50]}...")

        # 判断是否需要分解任务
        if self._need_decompose(task):
            return self._dispatch_with_decompose(task)
        else:
            return self._dispatch_direct(task)

    def handoff(
        self, from_agent: str, to_agent: str, task: str, context: list[dict]
    ) -> str:
        """处理 Agent 之间的交接（必须经过协调器）"""

        logger.info(f"[Coordinator] 交接: {from_agent} -> {to_agent}")

        # 验证目标 Agent 存在
        target = self.agents.get(to_agent)
        if not target:
            return f"错误：Agent {to_agent} 不存在"

        # 构建传递的上下文（去除 system 消息避免重复）
        ctx = [m for m in context if m.get("role") != "system"]

        # 执行子任务
        result = target.run(task, context=ctx)

        logger.info(f"[Coordinator] 子任务完成，返回给 {from_agent}")
        return result

    def _dispatch_direct(self, task: str) -> str:
        """直接分发（单一 Agent）"""

        agent_name = self._select_agent(task)
        agent = self.agents.get(agent_name)

        if agent:
            logger.info(f"[Coordinator] 分发给: {agent_name}")
            return agent.run(task)

        return "没有 Agent 可以处理这个任务"

    def _dispatch_with_decompose(self, task: str) -> str:
        """分解任务后分发"""

        # 分解任务
        subtasks = self._decompose_task(task)
        logger.info(f"[Coordinator] 任务分解为 {len(subtasks)} 个子任务")

        results = []
        for i, subtask in enumerate(subtasks):
            logger.info(
                f"[Coordinator] 执行子任务 {i + 1}/{len(subtasks)}: {subtask[:30]}..."
            )

            agent_name = self._select_agent(subtask)
            agent = self.agents.get(agent_name)

            if agent:
                result = agent.run(subtask)
                results.append({"task": subtask, "agent": agent_name, "result": result})
                logger.info(f"[Coordinator] 子任务 {i + 1} 完成")

        # 合并结果
        return self._merge_results(task, results)

    def _need_decompose(self, task: str) -> bool:
        """判断是否需要分解任务"""

        prompt = f"""判断以下任务是否需要分解为多个子任务才能完成。
如果需要不同专业能力的子任务，回答"需要"。如果一个 Agent 能完成，回答"不需要"。

任务：{task}

只需要回答"需要"或"不需要"。"""

        response = chat_completions(
            cfg=self.cfg,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )

        content = (
            (response.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return "需要" in content

    def _decompose_task(self, task: str) -> list[str]:
        """分解任务"""

        prompt = f"""将以下任务分解为多个子任务，每个子任务由一个专业 Agent 独立完成。
列出子任务，每行一个。

任务：{task}

只需要返回子任务列表。"""

        response = chat_completions(
            cfg=self.cfg,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )

        content = (
            (response.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        # 解析子任务
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        # 过滤掉可能的编号
        subtasks = []
        for line in lines:
            # 去掉 "1." "2." 等前缀
            import re

            cleaned = re.sub(r"^\d+[.)]\s*", "", line)
            if cleaned:
                subtasks.append(cleaned)

        return subtasks if subtasks else [task]

    def _select_agent(self, task: str) -> str:
        """为任务选择合适的 Agent"""

        options = "\n".join(
            [f"- {name}: {agent.spec.specialty}" for name, agent in self.agents.items()]
        )

        prompt = f"""从以下 Agent 选择最合适的一个来处理这个任务。

{options}

任务：{task}

只需要返回 Agent 名称。"""

        response = chat_completions(
            cfg=self.cfg,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )

        content = (
            (response.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        for name in self.agents.keys():
            if name in content:
                return name

        return list(self.agents.keys())[0]

    def _merge_results(self, original_task: str, results: list[dict]) -> str:
        """合并子任务结果"""

        if len(results) == 1:
            return results[0]["result"]

        combined = "\n\n".join(
            [
                f"## 子任务 {i + 1}: {r['task']}\n({r['agent']} 完成)\n\n{r['result']}"
                for i, r in enumerate(results)
            ]
        )

        prompt = f"""原始任务：{original_task}

以下是各子任务的结果：

{combined}

请综合给出最终答案。"""

        response = chat_completions(
            cfg=self.cfg,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )

        return (
            (response.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

    def list_agents(self) -> list[str]:
        """列出所有 Agent"""
        return [f"{name} ({a.spec.specialty})" for name, a in self.agents.items()]


__all__ = ["AgentSpec", "MiniManus", "Coordinator"]
