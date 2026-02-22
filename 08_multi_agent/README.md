# 08 Multi-Agent

这节课在上一课的基础上，引入了**多 Agent 协作**机制。每个 Agent 都是一个完整的 MiniManus，由协调器（Coordinator）来分配任务。

## 核心架构：Coordinator 中心模式

```
┌─────────────────────────────────────────────────────┐
│                  Coordinator                        │
│              （中心 Hub，所有跨 Agent 通讯）         │
└─────────────────────────────────────────────────────┘
         ↑              ↑              ↑
         │              │              │
    ┌────┴────┐   ┌───┴───┐   ┌────┴─────┐
    │ Coder  │   │Searcher│   │ Analyzer │
    └────────┘   └────────┘   └──────────┘
```

**核心设计原则**：
- **协调者居中**：Coordinator 是所有跨 Agent 通讯的 Hub
- **禁止直连**：子 Agent 之间不允许相互通讯，所有通讯必须经过 Coordinator
- **简化复杂度**：避免 Agent 之间相互调用带来的复杂度提升

## 运行

```bash
cd exercise

# 测试多 Agent 协调器
uv run python 08_multi_agent/main.py --task "搜索最近的AI新闻"

# 测试编程 Agent
uv run python 08_multi_agent/main.py --task "写一个斐波那契函数"

# 测试分析 Agent
uv run python 08_multi_agent/main.py --task "分析Python和JavaScript的区别"

# 测试复杂任务（自动分解）
uv run python 08_multi_agent/main.py --task "搜索AI最新消息并分析" --max-steps 5
```

## 核心设计

### 1. 统一架构：每个 Agent 都是 MiniManus

```python
# 每个 Agent 都有独立的工具配置
coder = MiniManus(coder_spec, cfg, coder_tools)      # Coder 的工具
searcher = MiniManus(searcher_spec, cfg, searcher_tools)  # Searcher 的工具
analyzer = MiniManus(analyzer_spec, cfg, analyzer_tools)  # Analyzer 的工具
```

### 2. 协调器（Coordinator）负责任务分配

```python
# 协调器通过 LLM 智能分配任务
coordinator = Coordinator()

# 核心功能：
# 1. 任务分解：判断任务是否需要分解为子任务
# 2. 任务分发：将子任务分配给合适的 Agent
# 3. 结果收集：收集各 Agent 的执行结果
# 4. 结果合并：将结果合并为最终答案
coordinator.dispatch(task)  # 自动选择最合适的 Agent
```

### 3. 任务流转流程

```python
# 用户任务 -> Coordinator -> 判断是否需要分解
#   -> 不需要：直接分发给单个 Agent
#   -> 需要：分解为多个子任务，依次分发、收集、合并
```

## 已注册的 Agent

| Agent | 专业 | 工具配置 |
|-------|------|----------|
| **Coder** | 编程开发 | search + terminate |
| **Searcher** | 信息搜索 | search + terminate |
| **Analyzer** | 分析总结 | search + terminate |

## 使用示例

### 1. 简单任务（直接分发）

```bash
uv run python 08_multi_agent/main.py --task "搜索AI的最新消息"
```

输出：
```
[Coordinator] 注册 Agent: Coder (编程开发)
[Coordinator] 注册 Agent: Searcher (信息搜索)
[Coordinator] 注册 Agent: Analyzer (分析总结)
...
[Coordinator] 收到任务: 搜索AI的最新消息
[Coordinator] 判断：任务简单，直接分发
[Coordinator] 分发给: Searcher
[Searcher] 开始处理任务
[Searcher] 任务完成
```

### 2. 复杂任务（自动分解）

```bash
uv run python 08_multi_agent/main.py --task "搜索AI最新消息并分析" --max-steps 5
```

输出：
```
[Coordinator] 收到任务: 搜索AI最新消息并分析
[Coordinator] 判断：任务需要分解为子任务
[Coordinator] 分解为: ['搜索AI最新消息', '分析搜索结果']
[Coordinator] 分发子任务 1/2: 搜索AI最新消息 -> Searcher
[Searcher] 开始处理子任务
[Searcher] 子任务完成
[Coordinator] 收集子任务结果: 1/2 完成
[Coordinator] 分发子任务 2/2: 分析搜索结果 -> Analyzer
[Analyzer] 开始处理子任务
[Analyzer] 子任务完成
[Coordinator] 收集子任务结果: 2/2 完成
[Coordinator] 合并结果...
[Coordinator] 最终结果: ...
```

### 3. 编程任务

```bash
uv run python 08_multi_agent/main.py --task "写一个快速排序函数"
```

### 4. 分析任务

```bash
uv run python 08_multi_agent/main.py --task "分析RAG和上下文工程的区别"
```

## 技术要点

- **AgentSpec**: 定义 Agent 的规格（名称、专业、描述）
- **MiniManus**: 完整的 Agent 实现，有自己的工具配置
- **Coordinator**: 
  - 协调器，通过 LLM 智能分配任务
  - 任务分解：判断任务是否需要分解
  - 结果合并：汇总各 Agent 结果
- **request_help 工具**: Agent 可以请求 Coordinator 派发给其他 Agent

## 本课重点

- 每个 Agent 都是一个完整的 MiniManus
- **Coordinator 是中心 Hub**：所有跨 Agent 通讯必须经过协调者
- **禁止直连**：子 Agent 之间不允许相互通讯
- 协调器负责任务分解、分发、收集、合并
- Agent 可以有不同工具配置
