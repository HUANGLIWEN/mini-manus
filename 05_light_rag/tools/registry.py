"""工具注册表"""

from .base import BaseTool
from .rag import RAGTool
from .terminate import TerminateTool

_terminate = TerminateTool()
_rag = RAGTool()

TOOL_REGISTRY: dict[str, BaseTool] = {
    "terminate": _terminate,
    "rag": _rag,
}
