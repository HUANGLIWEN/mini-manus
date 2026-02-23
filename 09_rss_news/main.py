"""Lesson 09: RSS News Agent - 入口"""

import argparse
import sys
from pathlib import Path

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from env import find_and_load_env
from openai_compat import load_config_from_env
from log import init_logger
from loguru import logger

from agent import create_multi_agent_system


def main():
    parser = argparse.ArgumentParser(description="Lesson 09: RSS News Agent")
    parser.add_argument("--task", default="生成今日AI新闻简报", help="任务描述")
    parser.add_argument("--max-steps", type=int, default=20, help="最大步数")
    parser.add_argument("--log-dir", type=str, default=None, help="日志目录")
    args = parser.parse_args()

    # 日志目录
    log_dir = Path(args.log_dir) if args.log_dir else Path(__file__).parent / "logs"

    init_logger(log_dir)
    find_and_load_env()
    cfg = load_config_from_env()

    # 创建多 Agent 系统
    coordinator = create_multi_agent_system(cfg)

    logger.info("=" * 60)
    logger.info("RSS News Agent 启动")
    logger.info("=" * 60)
    logger.info(f"已注册 Agent: {coordinator.list_agents()}")

    # 执行任务
    result = coordinator.dispatch(args.task)

    logger.info("*" * 60)
    logger.info("* 最终答案")
    logger.info("*" * 60)
    logger.info(result)


if __name__ == "__main__":
    main()
