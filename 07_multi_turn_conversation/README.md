# 07 Multi-turn Conversation

这节课在上一课的基础上，引入了**多轮对话**机制，支持会话管理和任务队列。

## 运行

```bash
cd exercise

# 单任务模式（会话连续）
uv run python 07_multi_turn_conversation/main.py --task "帮我写一个斐波那契函数"

# 指定会话 ID（继续之前的对话）
uv run python 07_multi_turn_conversation/main.py --task "改成迭代版本" --session-id "fib"

# 使用任务队列
uv run python 07_multi_turn_conversation/main.py --enqueue "写斐波那契"
uv run python 07_multi_turn_conversation/main.py --enqueue "写快速排序"
uv run python 07_multi_turn_conversation/main.py --run-queue
```

## 目录结构

```
exercise/
├── lib/                    # 公共库
│   ├── env.py
│   ├── openai_compat.py
│   └── log.py
├── 07_multi_turn_conversation/
│   ├── agent.py            # Agent 核心逻辑（支持会话管理）
│   ├── main.py            # 入口（支持任务队列）
│   ├── tools/             # 工具模块
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── search.py      # 搜索工具
│   │   └── terminate.py
│   ├── message/           # 消息模块
│   │   ├── __init__.py
│   │   ├── message_store.py  # SQLite 存储（支持会话列表）
│   │   └── compression.py   # LLM 压缩
│   └── task/              # 任务队列模块
│       └── task_queue.py
└── .env
```

## 核心功能

| 功能 | 说明 |
|------|------|
| **会话管理** | Session ID 隔离不同对话 |
| **任务队列** | 支持多任务连续执行 |
| **会话列表** | 可查看所有活跃会话 |
| **压缩继承** | 自动继承 Lesson 06 的压缩功能 |

## 多轮对话类型

| 类型 | 场景 | 支持 |
|------|------|------|
| **类型一：会话连续** | 继续之前的对话 | ✅ |
| **类型二：任务队列** | 批量执行多任务 | ✅ |
| **类型三：Human in the Loop** | 向用户确认 | 📖 文章介绍 |

## 使用示例

### 1. 会话连续

```bash
# 第一轮
uv run python 07_multi_turn_conversation/main.py --task "写斐波那契" --session-id "fib"

# 第二轮（记住上文）
uv run python 07_multi_turn_conversation/main.py --task "改成迭代" --session-id "fib"

# 第三轮
uv run python 07_multi_turn_conversation/main.py --task "加缓存" --session-id "fib"
```

### 2. 多会话隔离

```bash
# 会话 A
uv run python 07_multi_turn_conversation/main.py --task "斐波那契" --session-id "a"

# 会话 B（独立）
uv run python 07_multi_turn_conversation/main.py --task "排序" --session-id "b"
```

### 3. 任务队列

```bash
# 添加任务
uv run python 07_multi_turn_conversation/main.py --enqueue "任务1: 斐波那契"
uv run python 07_multi_turn_conversation/main.py --enqueue "任务2: 快速排序"

# 查看队列
uv run python 07_multi_turn_conversation/main.py --list-queue

# 执行队列
uv run python 07_multi_turn_conversation/main.py --run-queue
```

### 4. 查看会话列表

```bash
uv run python 07_multi_turn_conversation/main.py --list-sessions
```

输出示例：
```
共有 2 个会话：

Session ID           消息数     最后活跃              
--------------------------------------------------
fib                 6          2026-02-16 11:00:00
sort                2          2026-02-16 10:30:00
```

## 技术栈

- **消息存储**: SQLite
- **会话管理**: Session ID
- **任务队列**: JSON 文件持久化
- **压缩方式**: LLM 摘要（有损）

## 本课重点

- 多轮对话的三种类型
- Session ID 会话隔离
- 任务队列批量执行
- 与上下文工程（Lesson 06）结合
