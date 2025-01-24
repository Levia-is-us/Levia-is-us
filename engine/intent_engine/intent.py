from openai import OpenAI
import os
import sys
from dotenv import load_dotenv
from engine.llm_provider.llm import chat_completion
from engine.prompt_provider import messages

from engine.tool_framework.tool_registry import ToolRegistry
from engine.tool_framework.tool_caller import ToolCaller
from memory.episodic_memory.episodic_memory import (
    retrieve_short_pass_memory,
    store_long_pass_memory,
    retrieve_long_pass_memory
)
from engine.dbconnection.mysql_connector import MySQLPool
from engine.prompt_provider import system_message, check_plan_fittable_prompt, next_step_prompt, check_tools_result_prompt
from engine.flow.evaluator.evaluator_docgen_flow import extract_json_from_doc


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

                replyForUserInfo = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
                
                replyForUserInfo = eval(replyForUserInfo)

                print(f"replyForUserInfo: {replyForUserInfo}")

                # Get and display response
                # reply = response.choices[0].message.content
                if replyForUserInfo["type"] == "direct_answer":
                    print(f"\033[92mAssistant: {replyForUserInfo['response']}\033[0m")
                    continue
                elif replyForUserInfo["type"] == "intent_summary":
                    summary = replyForUserInfo["summary"]
                    execution_records_str = []
                    
                    memories = retrieve_long_pass_memory(summary)
                    high_score_memories = self.filter_high_score_memories(memories)

                    if high_score_memories:
                        # Get the first (highest scoring) memory
                        top_memory = high_score_memories[0]
                        execution_record_str = top_memory["metadata"]["execution_records"]
                        execution_records = [eval(record) for record in top_memory["metadata"]["execution_records"]]

                        memories_check_prompt = [{"role": "system", "content": check_plan_fittable_prompt}]
                        memories_check_prompt.append({"role": "user", "content": f"Intent A: {summary}"})
                        memories_check_prompt.append({"role": "user", "content": f"Intent B: {top_memory['id']}"})
                        memories_check_prompt.append({"role": "user", "content": f"Proposed Solution: {execution_records}"})

                        memories_check_result = chat_completion(memories_check_prompt, model="deepseek-chat", config={"temperature": 0.7})
                        try:
                            memories_check_result = eval(memories_check_result)
                        except:
                            memories_check_result = extract_json_from_doc(memories_check_result)
                        # print(f"memories_check_result: {memories_check_result}")
                        if memories_check_result["solution_sufficient"]['result'] == True or memories_check_result["solution_sufficient"]['result'] == "true":

                            for execution_record in execution_records:
                                try:
                                    # Parse the execution record string back to dictionary if needed
                                    if isinstance(execution_record, str):
                                        execution_record = eval(execution_record)
                                    
                                    result, record = self.execute_and_record_tool(
                                        execution_record,
                                        execution_record["tool"],
                                        execution_record["method"],
                                        execution_record["args"]
                                    )
                                    
                                    print(f"Executed tool: {execution_record['tool']}.{execution_record['method']}")
                                    print(f"Result: {result}")
                                    
                                except Exception as e:
                                    print(f"Error processing execution record: {str(e)}")
                                    continue
                        else:
                            memories = retrieve_short_pass_memory(replyForUserInfo)
                            print(f"retrieve_short_pass_memory: {memories}")
                            self.messages.append({"role": "system", "content": system_message})
                            reply = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
                            print(f"\033[92mAssistant: {reply}\033[0m")

                            try:
                                import json
                                tool_response = json.loads(reply)
                                tool_name = tool_response.get("tool")
                                tool_method = tool_response.get("method")
                                tool_args = tool_response.get("arguments", {})
                                tool_record = {'tool': tool_name, 'method': tool_method, 'args': tool_args}
                                print(f"tool_args: {tool_args}")
                                
                                if tool_name and tool_method:
                                    print(f"toolname: {tool_name}.{tool_method} args: {tool_args}")
                                    result, execution_record = self.execute_and_record_tool(
                                        tool_record,
                                        tool_name, 
                                        tool_method, 
                                        tool_args
                                    )
                                    execution_records.append(execution_record)
                                    
                            except Exception as e:
                                print(f"\033[91mError parsing JSON: {str(e)}\033[0m")
                                continue
                    else:
                        memories = retrieve_short_pass_memory(replyForUserInfo)
                        print(f"retrieve_short_pass_memory: {memories}")
                        self.messages.append({"role": "system", "content": system_message})
                        reply = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
                        print(f"\033[92mAssistant: {reply}\033[0m")

                        try:
                            import json
                            tool_response = json.loads(reply)
                            tool_name = tool_response.get("tool")
                            tool_method = tool_response.get("method")
                            tool_args = tool_response.get("arguments", {})
                            tool_record = {'tool': tool_name, 'method': tool_method, 'args': tool_args}
                            print(f"tool_args: {tool_args}")
                            
                            if tool_name and tool_method:
                                print(f"toolname: {tool_name}.{tool_method} args: {tool_args}")
                                result, execution_record = self.execute_and_record_tool(
                                    tool_record,
                                    tool_name, 
                                    tool_method, 
                                    tool_args
                                )
                                execution_records_str.append(execution_record)
                                
                        except Exception as e:
                            print(f"\033[91mError parsing JSON: {str(e)}\033[0m")

                    store_long_pass_memory(summary, summary, {"execution_records": execution_records_str})

                # Save assistant reply to current session
                # self.messages.append({"role": "assistant", "content": reply})


            except KeyboardInterrupt:
                print("\n\033[93mProgram terminated\033[0m")
                sys.exit(0)
            except Exception as e:
                print(f"\033[91mError occurred: {str(e)}\033[0m")
                # import traceback
                # print(f"\033[91mDetailed error:\n{traceback.format_exc()}\033[0m")

    def filter_high_score_memories(self, memories, threshold=0):
        """
        Filter and sort memories by score
        
        Args:
            memories: Memory matches dictionary
            threshold: Minimum score threshold (default: 0.9)
            
        Returns:
            list: Sorted high score matches in descending order
        """
        if not memories or 'matches' not in memories:
            return []
        
        high_score_matches = [
            match for match in memories['matches'] 
            if match.get('score', 0) >= threshold
        ]
        
        # Sort matches by score in descending order
        sorted_matches = sorted(
            high_score_matches,
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        
        return sorted_matches

    def execute_and_record_tool(self, execution_record, tool_name, tool_method, tool_args):
        """
        Execute tool and record execution results
        
        Args:
            tool_name: Name of the tool
            tool_method: Method to be executed
            tool_args: Arguments for the tool        
        Returns:
            tuple: (execution_result, execution_record)
        """
        print(f"execution_record: {execution_record}")
        result = self.caller.call_tool(tool_name=tool_name, method=tool_method, kwargs=tool_args)
        print(f"tool result: {result}")
        llm_check_prompt = check_tools_result_prompt(tool_excution=f"{execution_record}", tool_output=result)
        llm_confirmation = chat_completion(llm_check_prompt, model="deepseek-chat", config={"temperature": 0.7})
        print(f"llm_confirmation: {llm_confirmation}")

        try:
            llm_confirmation = eval(llm_confirmation)
        except:
            llm_confirmation = extract_json_from_doc(llm_confirmation)

        execution_record = {
            "tool": tool_name,
            "method": tool_method,
            "args": tool_args,
            "result": result,
            "status": "success" if llm_confirmation["status"] == "success" else "failure"
        }
        
        # Record to database
        sql = """
            INSERT INTO levia_tool_excutor_history 
            (toolId, uid, tool_excute_args, tool_response, creatTime) 
            VALUES (%s, %s, %s, %s, now())
        """
        tool_id = tool_name + tool_method
        db_pool.execute(sql, (tool_id, '123', str(tool_args), str(result)))
        
        return result, str(execution_record)