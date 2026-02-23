"""对话压缩模块"""

from typing import Any

from loguru import logger


def estimate_tokens(text: str) -> int:
    """简单估算 token 数量（1 token ≈ 4 字符）"""
    return len(text) // 4


def should_compress(messages: list[dict], max_tokens: int = 4000) -> bool:
    """判断是否需要压缩"""
    total = sum(estimate_tokens(m.get("content", "")) for m in messages)
    return total > max_tokens


def compress_conversation(messages: list[dict], cfg) -> list[dict]:
    """
    压缩对话历史

    核心算法：
    1. 保留 system 消息（系统指令）
    2. 保留用户最后一条消息（当前意图）
    3. 把中间所有消息压缩成摘要
    """
    if len(messages) <= 3:
        return messages

    # 找到用户最后一条消息
    last_user_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            last_user_idx = i
            break

    if not last_user_idx or last_user_idx <= 1:
        return messages

    # 提取需要压缩的消息
    to_compress = messages[1:last_user_idx]

    # 生成摘要
    conversation_text = "\n".join(
        f"{m['role']}: {m['content'][:200]}" for m in to_compress
    )

    prompt = f"""请用一句话总结以下对话的核心要点（不超过 50 字）：

{conversation_text}

只需返回摘要，不要其他内容。"""

    logger.info(f"[压缩] 正在调用 LLM 压缩 {len(to_compress)} 条消息...")

    # 使用内置的 chat_completions 避免循环依赖
    from openai_compat import chat_completions

    summary_resp = chat_completions(
        cfg=cfg,
        messages=[{"role": "user", "content": prompt}],
        tools=None,
    )

    summary = (
        (summary_resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
    )

    logger.info(f"[压缩] LLM 返回摘要: {summary[:100]}...")

    # 构建压缩后的消息列表
    compressed = [
        messages[0],  # system
        {"role": "system", "content": f"[历史摘要] {summary}"},
        messages[last_user_idx],  # 用户最新消息
    ]

    return compressed
