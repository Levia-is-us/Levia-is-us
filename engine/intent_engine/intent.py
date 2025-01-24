from openai import OpenAI
import os
import sys
from dotenv import load_dotenv
from engine.llm_provider.llm import chat_completion
from engine.prompt_provider import messages

from engine.tool_framework.tool_registry import ToolRegistry
from engine.tool_framework.tool_caller import ToolCaller
from memory.episodic_memory.episodic_memory import (
    store_short_pass_memory,
    retrieve_short_pass_memory,
    store_long_pass_memory,
    retrieve_long_pass_memory
)
from engine.dbconnection.mysql_connector import MySQLPool

db_pool = MySQLPool()

class ChatClient:
    def __init__(self):
        # Try to get API key from environment variable
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        self.api_key = os.getenv("OPENAI_API_KEY")
        print(f"api_key: {self.api_key}")
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
                # response = self.client.chat.completions.create(
                #     model="deepseek-chat",
                #     messages=self.messages,
                #     temperature=0.7
                # )

                reply = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})

                # Get and display response
                # reply = response.choices[0].message.content
                print(f"\033[92mAssistant: {reply}\033[0m")

                try:
                    import json
                    tool_response = json.loads(reply)
                    tool_name = tool_response.get("tool")
                    tool_method = tool_response.get("method")
                    tool_args = tool_response.get("arguments", {})
                    print(f"tool_args: {tool_args}")
                    
                    execution_records = list()
                    
                    if tool_name and tool_method:
                        print(f"toolname: {tool_name}.{tool_method} args: {tool_args}")
                        result = self.caller.call_tool(tool_name=tool_name, method=tool_method, kwargs=tool_args)
                        print(f"tool result: {result}")
                        llm_confirmation = input("tool execution success or failure? (y/n): ")
                        
                        execution_record = {
                            "tool": tool_name,
                            "method": tool_method,
                            "args": tool_args,
                            "result": result,
                            "status": "success" if llm_confirmation == "y" else "failure"
                        }
                        execution_records.append(str(execution_record))
                        
                        if llm_confirmation == "y":
                            result["status"] = "success"
                        else:
                            result["status"] = "failure"
                            # store_short_pass_memory(tool_name + tool_method, tool_response.get("desc"), {"status": "success"})
                        # 使用参数化查询来防止SQL注入并正确处理特殊字符
                        sql = """
                            INSERT INTO levia_tool_excutor_history 
                            (toolId, uid, tool_excute_args, tool_response, creatTime) 
                            VALUES (%s, %s, %s, %s, now())
                        """
                        tool_id = tool_name + tool_method
                        db_pool.execute(sql, (tool_id, '123', str(tool_args), str(result)))
                            
                except Exception as e:
                    print(f"\033[91mError parsing JSON: {str(e)}\033[0m")

                store_long_pass_memory(user_input, user_input, {"execution_records": execution_records})
                memories = retrieve_long_pass_memory(user_input)
                print(f"retrieve_long_pass_memory: {memories}")

                # Save assistant reply to current session
                # self.messages.append({"role": "assistant", "content": reply})


            except KeyboardInterrupt:
                print("\n\033[93mProgram terminated\033[0m")
                sys.exit(0)
            except Exception as e:
                print(f"\033[91mError occurred: {str(e)}\033[0m")
                # import traceback
                # print(f"\033[91mDetailed error:\n{traceback.format_exc()}\033[0m")