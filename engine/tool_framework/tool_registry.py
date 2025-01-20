import sys
import json
import inspect
import importlib.util
import os
from typing import Dict, Any, Optional, Callable, Type, List
from .base_tool import BaseTool


from pathlib import Path
class ToolRegistry:
    """Central registry for all tools"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tools = {}
            cls._instance.tool_paths = {}
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'tools'):
            self.tools: Dict[str, Type[BaseTool]] = {}
            self.tool_paths: Dict[str, str] = {}

    def register_tool(self, tool_class: Type[BaseTool], tool_path: str) -> None:
        """Register a tool class"""
        tool_name = tool_class.__name__
        self.tools[tool_name] = tool_class
        self.tool_paths[tool_name] = tool_path

    def get_tool(self, tool_name: str) -> Optional[Type[BaseTool]]:
        """Get a tool class by name"""
        return self.tools.get(tool_name)

    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """Get tool script path by name"""
        return self.tool_paths.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools and their methods"""
        tools_info = []
        for tool_name, tool_class in self.tools.items():
            tool = tool_class()
            tool_info = {
                "name": tool_name,
                "description": tool.description,
                "path": self.tool_paths[tool_name],
                "methods": {
                    name: {
                        "description": tool.get_method_description(name),
                        "signature": str(inspect.signature(method))
                    }
                    for name, method in tool.methods.items()
                }
            }
            tools_info.append(tool_info)
        return tools_info

    def scan_directory(self, directory: str) -> None:
        """扫描目录及其子目录下的所有工具文件并注册"""
        # 获取目录下所有Python文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                # 检查是否是工具文件(以_tool.py结尾)
                if file.endswith('_tool.py'):
                    tool_file = Path(root) / file
                    try:
                        # 加载模块
                        spec = importlib.util.spec_from_file_location(
                            tool_file.stem, str(tool_file))
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # 查找并注册工具类
                        for item_name in dir(module):
                            item = getattr(module, item_name)
                            if (inspect.isclass(item) and 
                                issubclass(item, BaseTool) and 
                                item != BaseTool):
                                self.register_tool(item, str(tool_file))
                    except Exception as e:
                        print(f"加载工具 {tool_file} 时出错: {e}", file=sys.stderr)