"""工具注册表"""

from .base import BaseTool
from .terminate import TerminateTool

_terminate = TerminateTool()

TOOL_REGISTRY: dict[str, BaseTool] = {
    "terminate": _terminate,
}
