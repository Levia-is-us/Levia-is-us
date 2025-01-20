from tool_framewotk.tool_run import run_tool
from tool_framewotk.tool_registry import ToolRegistry
from tool_framewotk.tool_caller import ToolCaller
import os


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
