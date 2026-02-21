"""Lesson 07: Multi-turn Conversation - 入口"""

import argparse
from pathlib import Path

from agent import MiniManus
from task import TaskQueue


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lesson 07: Multi-turn Conversation - Session & Task Queue"
    )
    parser.add_argument("--task", help="The user task for the agent to solve.")
    parser.add_argument(
        "--session-id",
        type=str,
        default="default",
        help="Session ID for conversation history.",
    )
    parser.add_argument(
        "--max-steps", type=int, default=10, help="Safety brake for the agent loop."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="Max tokens before compression.",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory for log files (default: ./logs in lesson dir).",
    )
    parser.add_argument(
        "--enqueue",
        type=str,
        help="Add task to queue instead of running immediately.",
    )
    parser.add_argument(
        "--run-queue",
        action="store_true",
        help="Run all tasks in the queue.",
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all existing sessions.",
    )
    parser.add_argument(
        "--list-queue",
        action="store_true",
        help="List all tasks in the queue.",
    )
    parser.add_argument(
        "--clear-queue",
        action="store_true",
        help="Clear the task queue.",
    )
    args = parser.parse_args()

    # 设置日志目录
    if args.log_dir:
        log_dir = Path(args.log_dir)
    else:
        log_dir = Path(__file__).parent / "logs"

    # 创建 Agent 实例
    agent = MiniManus(
        max_steps=args.max_steps, log_dir=log_dir, max_tokens=args.max_tokens
    )

    # 任务队列
    queue = TaskQueue()

    # 列出所有会话
    if args.list_sessions:
        from message import MessageStore

        db_path = Path(__file__).parent / "message" / "messages.db"
        store = MessageStore(str(db_path))
        sessions = store.list_sessions()

        if not sessions:
            print("暂无会话")
            return 0

        print(f"共有 {len(sessions)} 个会话：\n")
        print(f"{'Session ID':<20} {'消息数':<10} {'最后活跃':<20}")
        print("-" * 50)
        for s in sessions:
            print(f"{s['session_id']:<20} {s['msg_count']:<10} {s['last_active']:<20}")
        return 0

    # 列出队列任务
    if args.list_queue:
        tasks = queue.list_tasks()
        if not tasks:
            print("队列为空")
            return 0

        stats = queue.get_stats()
        print(
            f"队列统计: 待处理 {stats['pending']}, 进行中 {stats['running']}, "
            f"已完成 {stats['completed']}, 失败 {stats['failed']}\n"
        )

        print(f"{'状态':<12} {'任务':<40} {'会话':<15}")
        print("-" * 70)
        for t in tasks:
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
            }
            icon = status_icon.get(t["status"], "❓")
            print(f"{icon} {t['status']:<8} {t['task'][:38]:<40} {t['session_id']:<15}")
        return 0

    # 清空队列
    if args.clear_queue:
        queue.clear()
        print("[队列] 已清空")
        return 0

    # 添加任务到队列
    if args.enqueue:
        queue.add(args.enqueue, args.session_id)
        return 0

    # 运行队列
    if args.run_queue:
        print("[队列] 开始执行任务队列\n")
        while queue.has_pending():
            task_info = queue.pop()
            task = task_info["task"]
            session_id = task_info.get("session_id", "default")

            print(f"\n{'=' * 60}")
            print(f"[队列] 执行任务: {task}")
            print(f"[队列] 会话: {session_id}")
            print(f"{'=' * 60}\n")

            try:
                agent.run(task=task, session_id=session_id)
                queue.complete(task)
            except Exception as e:
                queue.fail(task, str(e))
                print(f"[错误] {e}")

        print("\n[队列] 所有任务已完成")
        return 0

    # 单任务模式
    if args.task:
        agent.run(task=args.task, session_id=args.session_id)
        return 0

    # 没有指定任务
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
