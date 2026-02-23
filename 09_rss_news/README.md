# 09 RSS News Agent

这是课程的最后一课，我们将之前 8 课学到的所有知识整合起来，基于 **MiniManus 架构**构建一个**能实际工作的 RSS 新闻简报 Agent**。

## 核心架构

基于 Lesson 08 的 Multi-Agent 模式，构建了 4 个专业 Agent：

```
┌─────────────────────────────────────────────────────┐
│                  Coordinator                        │
│              （中心 Hub，所有跨 Agent 通讯）         │
└─────────────────────────────────────────────────────┘
         ↑              ↑              ↑           ↑
         │              │              │           │
    ┌────┴────┐   ┌───┴───┐   ┌────┴─────┐  ┌──┴────┐
    │ Fetcher │   │ Filter │   │Summarizer│  │Reporter│
    └────────┘   └────────┘   └──────────┘  └───────┘
```

| Agent | 功能 |
|-------|------|
| **Fetcher** | 获取 RSS 订阅源的文章（并行获取） |
| **Filter** | 让 Agent 自己判断内容相关性 |
| **Summarizer** | 生成文章摘要 |
| **Reporter** | 生成每日简报 |

## 技术特点

- **并行获取**：使用 `ThreadPoolExecutor` 并行抓取多个 RSS 源
- **LLM 过滤**：Agent 自己判断内容是否相关，而非硬编码关键词
- **任务分解**：Coordinator 自动用 LLM 分解复杂任务
- **Agent 协作**：子任务由不同专业 Agent 完成

## 工具注册

RSS News Agent 注册了以下工具：

| 工具 | 功能 |
|------|------|
| `rss_fetch` | 获取 RSS 文章列表 |
| `rss_filter` | 过滤相关文章 |
| `rss_summarize` | 生成摘要 |
| `rss_report` | 生成简报 |
| `search` | 搜索工具 |
| `terminate` | 终止工具 |

## 运行

```bash
cd exercise

# 运行 RSS News Agent（默认任务：生成今日AI新闻简报）
uv run python 09_rss_news/main.py

# 自定义任务
uv run python 09_rss_news/main.py --task "搜索最新的 AI 新闻"

# 指定最大步数
uv run python 09_rss_news/main.py --max-steps 30
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--task` | `生成今日AI新闻简报` | 任务描述 |
| `--max-steps` | 20 | 最大步数 |
| `--log-dir` | `logs/` | 日志目录 |

## 输出示例

```
=====================================================================
RSS News Agent 启动
=====================================================================
已注册 Agent: ['Fetcher (RSS 获取)', 'Filter (内容过滤)', 'Summarizer (摘要生成)', 'Reporter (简报生成)']
[Coordinator] 收到主任务: 生成今日AI新闻简报
[Coordinator] 任务分解为 7 个子任务
[Coordinator] 执行子任务 1/7: 全网搜索并采集今日AI新闻原始数据...
[Fetcher] 开始处理任务...
[RSS] 加载源: simonwillison.net
[RSS] 加载源: jeffgeerling.com
...（并行加载多个源）
[RSS] Jeff Geerling - 10 篇文章
[RSS] Simon Willison's Weblog - 10 篇文章
[Fetcher] 任务完成
[Coordinator] 子任务 1 完成
[Coordinator] 执行子任务 2/7: 筛选高价值新闻并去除重复内容...
...
```

## 技术要点

- **基于 MiniManus**：继承前 8 课的所有能力
- **Multi-Agent**：4 个专业 Agent 协作
- **工具系统**：RSS 相关工具封装
- **Coordinator 模式**：所有 Agent 通过协调器通讯
- **并行获取**：ThreadPoolExecutor 并行抓取 RSS 源
- **LLM 过滤**：Agent 自己判断内容相关性
