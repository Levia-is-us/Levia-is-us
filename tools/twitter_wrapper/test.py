import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from engine.tool_framework import ToolRegistry, ToolCaller

def main():
    registry = ToolRegistry()
    
    # Use absolute path
    tools_dir = os.path.join(os.path.dirname(__file__), "./")
    registry.scan_directory(tools_dir)  # Scan tools directory

    # List available tools
    tools = registry.list_tools()
    print("Available tools:", len(tools))
    for tool in tools:
        print(f"Tool: {tool['name']}")
        print(f"Description: {tool['description']}")
        print("Methods:")
        for method, info in tool['methods'].items():
            print(f" - {method}{info['signature']}")

    # Create ToolCaller instance
    caller = ToolCaller(registry)
    
    print("\nCalling tweet tool...")
    result = caller.call_tool(
        tool_name="send_tweet_tool", 
        method="send_tweet", 
        kwargs={
            "tweet": "Hello, world!", 
            "username": "test", 
            "password": "test"
        }
    )
    
    if result:
        if 'error' in result:
            print(f"Tool execution error: {result['error']}")
        else:
            print(f"Response info: {result}")
    else:
        print("Tool call failed, no result returned")

if __name__ == "__main__":
    main()