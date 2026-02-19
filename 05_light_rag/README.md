# 05 Light RAG

这节课在上一课的基础上，引入了 **RAG**（检索增强生成），让 Agent 能够基于私有知识库回答问题。

## 运行

```bash
cd exercise

# 构建知识库
uv run python 05_light_rag/main.py --task "构建知识库，文档：1. Python 是一种高级编程语言 2. JavaScript 是 Web 开发语言 3. Rust 以安全性著称"

# 查询知识库
uv run python 05_light_rag/main.py --task "哪种语言以安全性著称？"
```

## 目录结构

```
exercise/
├── lib/                    # 公共库
│   ├── env.py
│   ├── openai_compat.py
│   └── log.py
├── 05_light_rag/
│   ├── agent.py            # Agent 核心逻辑（支持 RAG）
│   ├── main.py            # 入口
│   ├── rag_knowledge/    # FAISS 索引文件
│   │   ├── faiss.index
│   │   └── metadata.json
│   └── tools/             # 工具模块
│       ├── base.py
│       ├── registry.py
│       ├── rag.py         # RAG 工具
│       └── terminate.py
└── .env
```

## RAG 工具

| 操作 | 说明 |
|------|------|
| `rag(action="build", documents=[...])` | 构建知识库 |
| `rag(action="query", question="...")` | 查询知识库 |

## 技术栈

- **向量数据库**: FAISS（Facebook AI Similarity Search）
- **Embedding 模型**: Sentence Transformers (all-MiniLM-L6-v2, 384维)

## 本课重点

- RAG 核心原理
- FAISS 本地向量检索
- 向量相似度计算
- RAG vs 上下文记忆
