import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.tool_framework.tool_run import run_tool
from engine.tool_framework.tool_registry import ToolRegistry
from engine.tool_framework.tool_caller import ToolCaller


def main():
    # Create and initialize ToolRegistry
    registry = ToolRegistry()
    
    # Use absolute path
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    registry.scan_directory(tools_dir)  # Scan tools directory

    # Create ToolCaller instance
    caller = ToolCaller(registry)

    # List all available tools
    tools = registry.list_tools()
    print("Available tools:", len(tools))
    for tool in tools:
        print(f"Tool: {tool['name']}")
        print(f"Description: {tool['description']}")
        print("Methods:")
        for method, info in tool['methods'].items():
            print(f" - {method}{info['signature']}")

    # Call tool and handle result
    print("\nCalling location tool...")
    result = caller.call_tool(tool_name="LocationTool", method="get_current_location")
    
    if result:
        if 'error' in result:
            print(f"Tool execution error: {result['error']}")
        else:
            print(f"Location info: {result}")
    else:
        print("Tool call failed, no result returned")

if __name__ == "__main__":
    main()
