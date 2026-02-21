"""任务队列模块 - 支持多任务连续执行"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskQueue:
    """任务队列：支持多任务连续执行"""

    queue_file: Path = field(
        default_factory=lambda: Path(__file__).parent / "task_queue.json"
    )
    _queue: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self._load()

    def _load(self):
        """从文件加载队列"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file) as f:
                    self._queue = json.load(f)
            except json.JSONDecodeError:
                self._queue = []

    def _save(self):
        """保存队列到文件"""
        with open(self.queue_file, "w") as f:
            json.dump(self._queue, f, ensure_ascii=False, indent=2)

    def add(self, task: str, session_id: str = "default") -> int:
        """
        添加任务到队列

        Args:
            task: 任务描述
            session_id: 会话 ID

        Returns:
            队列中的任务数量
        """
        self._queue.append(
            {
                "task": task,
                "session_id": session_id,
                "status": "pending",
            }
        )
        self._save()
        print(f"[队列] 添加任务: {task[:50]}...")
        return len(self._queue)

    def pop(self) -> dict[str, Any] | None:
        """取出下一个待执行任务"""
        for item in self._queue:
            if item["status"] == "pending":
                item["status"] = "running"
                self._save()
                return item
        return None

    def complete(self, task: str):
        """标记任务完成"""
        for item in self._queue:
            if item["task"] == task:
                item["status"] = "completed"
                self._save()
                print(f"[队列] 完成任务: {item['task'][:50]}...")
                break

    def fail(self, task: str, error: str):
        """标记任务失败"""
        for item in self._queue:
            if item["task"] == task:
                item["status"] = "failed"
                item["error"] = error
                self._save()
                print(f"[队列] 任务失败: {item['task'][:50]}... 错误: {error}")
                break

    def has_pending(self) -> bool:
        """检查是否有待执行任务"""
        return any(item["status"] == "pending" for item in self._queue)

    def list_tasks(self) -> list[dict[str, Any]]:
        """列出所有任务"""
        return self._queue.copy()

    def clear(self, status: str | None = None):
        """
        清空队列

        Args:
            status: 如果指定，只清空指定状态的任务
        """
        if status is None:
            self._queue = []
        else:
            self._queue = [item for item in self._queue if item["status"] != status]
        self._save()

    def get_stats(self) -> dict[str, int]:
        """获取队列统计"""
        stats = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for item in self._queue:
            status = item.get("status", "pending")
            if status in stats:
                stats[status] += 1
        return stats
