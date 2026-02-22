"""Lesson 08: Multi-Agent - 入口"""

import argparse
from pathlib import Path

from agent import MiniManus


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lesson 08: Multi-Agent - Handoff & Router Pattern"
    )
    parser.add_argument(
        "--task", required=True, help="The user task for the agent to solve."
    )
    parser.add_argument(
        "--max-steps", type=int, default=10, help="Safety brake for the agent loop."
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory for log files (default: ./logs in lesson dir).",
    )
    args = parser.parse_args()

    # 设置日志目录
    if args.log_dir:
        log_dir = Path(args.log_dir)
    else:
        log_dir = Path(__file__).parent / "logs"

    agent = MiniManus(max_steps=args.max_steps, log_dir=log_dir)
    agent.run(task=args.task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
