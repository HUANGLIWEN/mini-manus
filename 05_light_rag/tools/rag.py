"""RAG Tool - 基于 FAISS + Sentence Transformers 的轻量级 RAG"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .base import BaseTool


class RAGTool(BaseTool):
    """RAG 工具：构建知识库、检索文档"""

    def __init__(self):
        # 使用本地文件存储
        self.db_path = Path(__file__).parent.parent / "rag_knowledge"
        self.db_path.mkdir(exist_ok=True)
        self.index_path = self.db_path / "faiss.index"
        self.meta_path = self.db_path / "metadata.json"

        # all-MiniLM-L6-v2: 384 维向量
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = 384

        # 加载已有索引
        self.index = None
        self.metadata: list[dict] = []
        self._load()

    def _load(self):
        """加载已有索引"""
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        if self.meta_path.exists():
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)

    def _save(self):
        """保存索引"""
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f)

    @property
    def name(self) -> str:
        return "rag"

    @property
    def description(self) -> str:
        return """RAG 工具：基于知识库回答问题。

actions:
- build: 构建知识库（输入：documents 文档列表，每项包含 content 和 source）
- query: 查询知识库（输入：question 问题）

示例：
rag(action="build", documents=[{"content": "Python 是编程语言", "source": "doc1"}])
rag(action="query", question="什么是 Python？")
"""

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["build", "query"],
                    "description": "操作类型：build 构建知识库，query 查询知识库",
                },
                "documents": {
                    "type": "array",
                    "description": "文档列表（build 动作需要）",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "文档内容"},
                            "source": {"type": "string", "description": "文档来源"},
                        },
                    },
                },
                "question": {
                    "type": "string",
                    "description": "查询问题（query 动作需要）",
                },
            },
            "required": ["action"],
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        action = kwargs.get("action", "")

        if action == "build":
            documents = kwargs.get("documents", [])
            return self._build_index(documents)
        elif action == "query":
            question = kwargs.get("question", "")
            return self._query(question)
        else:
            return False, f"Unknown action: {action}. Use 'build' or 'query'."

    def _build_index(self, documents: list[dict[str, Any]]) -> tuple[bool, str]:
        """构建知识库索引"""
        if not documents:
            return False, "No documents provided"

        # 向量化
        texts = [doc.get("content", "") for doc in documents]
        vectors = self.model.encode(texts)

        # 转换为 float32
        vectors = vectors.astype("float32")

        # 创建或追加到索引
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)  # 内积相似度

        # 归一化向量（用于余弦相似度）
        faiss.normalize_L2(vectors)

        # 添加到索引
        self.index.add(vectors)

        # 保存元数据
        for i, doc in enumerate(documents):
            self.metadata.append(
                {
                    "id": len(self.metadata),
                    "content": doc.get("content", ""),
                    "source": doc.get("source", f"doc_{i}"),
                }
            )

        # 保存
        self._save()

        return True, f"Indexed {len(documents)} documents"

    def _query(self, question: str) -> tuple[bool, str]:
        """查询知识库"""
        if not question:
            return False, "No question provided"

        if self.index is None or len(self.metadata) == 0:
            return False, "Knowledge base is empty. Please build it first."

        # 把问题转成向量
        question_vector = self.model.encode([question]).astype("float32")
        faiss.normalize_L2(question_vector)

        # 检索相似文档
        k = min(3, self.index.ntotal)
        distances, indices = self.index.search(question_vector, k)

        # 提取相关文档
        context_parts = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            meta = self.metadata[idx]
            content = meta["content"]
            source = meta["source"]
            distance = float(distances[0][i])
            context_parts.append(f"[{source}] (similarity: {distance:.4f})\n{content}")

        if not context_parts:
            return False, "No relevant documents found"

        context = "\n\n---\n\n".join(context_parts)

        # 返回上下文，供 LLM 生成答案
        return False, f"Relevant context:\n\n{context}"
