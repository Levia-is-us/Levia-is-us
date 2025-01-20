from openai import OpenAI
import os
import sys
from dotenv import load_dotenv
from engine.prompt_provider import messages

from engine.tool_framework.tool_registry import ToolRegistry
from engine.tool_framework.tool_caller import ToolCaller

class ChatClient:
    def __init__(self):
        # Try to get API key from environment variable
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.api_key = self._get_api_key()
        base_url = os.getenv("OPENAI_BASE_URL")
        if not base_url:
            print("\033[93mWarning: OPENAI_BASE_URL not found in .env file\033[0m")
        
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.messages = []
        registry = ToolRegistry()
    
        # Use absolute path
        tools_dir = os.path.join(project_root, "tools")
        print(f"Scanning tools from: {tools_dir}")
        registry.scan_directory(tools_dir)  # Scan tools directory

        # Create ToolCaller instance
        self.caller = ToolCaller(registry)

        tools = registry.list_tools()
        print("Available tools:", len(tools))
        for tool in tools:
            print(f"Tool: {tool['name']}")
            print(f"Description: {tool['description']}")
            print("Methods:")
            for method, info in tool['methods'].items():
                print(f" - {method}{info['signature']}")

    def _get_api_key(self) -> str:
        """Get API key from user input"""
        print("\033[93mPlease enter your OpenAI API key:\033[0m")
        api_key = input().strip()
        
        # Ask whether to save the API key
        save = input("Save API key to environment variables? (y/n): ").lower()
        if save == 'y':
            with open(os.path.expanduser("~/.bashrc"), "a") as f:
                f.write(f'\nexport OPENAI_API_KEY="{api_key}"\n')
            print("API key has been saved to ~/.bashrc")
            print("Please run 'source ~/.bashrc' or restart terminal to take effect")
        
        return api_key

    def chat(self):
        """Start interactive chat"""
        print("\033[93mWelcome to OpenAI Chat Program!\033[0m")
        print("Enter 'quit' to exit, 'clear' to reset current conversation")
        
        while True:
            try:
                
                # Get user input
                self.messages = messages.copy()
                user_input = input("\033[94mYou: \033[0m").strip()
                # Handle special commands
                if user_input.lower() == 'quit':
                    print("\033[93mGoodbye!\033[0m")
                    break
                elif user_input.lower() == 'clear':
                    self.messages = []
                    print("\033[93mConversation cleared\033[0m")
                    continue
                elif not user_input:
                    continue

                # Add user message
                self.messages.append({"role": "user", "content": user_input})

                # Call API for response
                print("\033[93mThinking...\033[0m")
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=self.messages,
                    temperature=0.7
                )

                # Get and display response
                reply = response.choices[0].message.content
                print(f"\033[92mAssistant: {reply}\033[0m")
                
                # 解析Assistant返回的JSON
                try:
                    import json
                    tool_response = json.loads(reply)
                    tool_name = tool_response.get("tool")
                    tool_method = tool_response.get("method")
                    tool_args = tool_response.get("arguments", {})
                    print(f"tool_args: {tool_args}")
                    
                    if tool_name and tool_method:
                        print(f"调用工具: {tool_name}.{tool_method}，参数: {tool_args}")
                        result = self.caller.call_tool(tool_name=tool_name, method=tool_method, kwargs=tool_args)
                        print(f"工具返回: {result}")
                except Exception as e:
                    print(f"\033[91mError parsing JSON: {str(e)}\033[0m")

                # Save assistant reply to current session
                # self.messages.append({"role": "assistant", "content": reply})


            except KeyboardInterrupt:
                print("\n\033[93mProgram terminated\033[0m")
                sys.exit(0)
            except Exception as e:
                print(f"\033[91mError occurred: {str(e)}\033[0m")
                # import traceback
                # print(f"\033[91mDetailed error:\n{traceback.format_exc()}\033[0m")