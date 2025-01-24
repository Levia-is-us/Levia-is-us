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
from engine.prompt_provider import system_message, check_plan_fittable_prompt, next_step_prompt, check_tools_result_prompt, intents_system_prompt, plan_maker_prompt
from engine.flow.evaluator.evaluator_docgen_flow import extract_json_from_doc


db_pool = MySQLPool()

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
        self._print_welcome_message()
        
        while True:
            try:
                user_input = self._handle_user_input()
                if user_input is None:  # User entered 'quit'
                    break
                    
                reply_info = self._get_initial_response()
                
                if reply_info["type"] == "direct_answer":
                    self._handle_direct_answer(reply_info)
                elif reply_info["type"] == "intent_summary":
                    self._handle_intent_summary(reply_info)
                    
            except KeyboardInterrupt:
                print("\n\033[93mProgram terminated\033[0m")
                sys.exit(0)
            except Exception as e:
                print(f"\033[91mError occurred: {str(e)}\033[0m")

    def _print_welcome_message(self):
        """Print welcome message"""
        print("\033[93mWelcome to OpenAI Chat Program!\033[0m")
        print("Enter 'quit' to exit, 'clear' to reset current conversation")

    def _handle_user_input(self):
        """Handle user input"""
        self.messages = messages.copy()
        user_input = input("\033[94mYou: \033[0m").strip()
        
        if user_input.lower() == 'quit':
            print("\033[93mGoodbye!\033[0m")
            return None
        elif user_input.lower() == 'clear':
            self.messages = []
            print("\033[93mConversation cleared\033[0m")
            return ''
        elif not user_input:
            return ''
        
        self.messages.append({"role": "user", "content": user_input})
        return user_input

    def _get_initial_response(self):
        """Get initial response from LLM"""
        self.messages.append({"role": "system", "content": intents_system_prompt})
        reply_info = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
        reply_info = eval(reply_info)
        # print(f"replyForUserInfo: {reply_info}")
        return reply_info

    def _handle_direct_answer(self, reply_info):
        """Handle direct answer type response"""
        print(f"\033[92mAssistant: {reply_info['response']}\033[0m")

    def _handle_intent_summary(self, reply_info):
        """Handle intent summary type response"""
        summary = reply_info["summary"]
        execution_records_str = []
        
        memories = retrieve_long_pass_memory(summary)
        high_score_memories = self.filter_high_score_memories(memories)
        
        if high_score_memories:
            self._process_existing_memories(high_score_memories, summary, execution_records_str)
        else:
            self._process_new_intent(summary, execution_records_str)
        
        store_long_pass_memory(summary, summary, {"execution_records": execution_records_str})

    def _process_existing_memories(self, high_score_memories, summary, execution_records_str):
        """Process existing memories from the database"""
        top_memory = high_score_memories[0]
        execution_records = [eval(record) for record in top_memory["metadata"]["execution_records"]]
        
        if self._check_solution_sufficient(summary, top_memory, execution_records):
            self._execute_existing_records(execution_records)
        else:
            plan = self._process_new_intent(summary)
            self._handle_new_tool_execution(execution_records_str, summary, plan)

    def _check_solution_sufficient(self, summary, top_memory, execution_records):
        """Check if the existing solution is sufficient for current intent"""
        memories_check_prompt = [
            {"role": "system", "content": check_plan_fittable_prompt},
            {"role": "user", "content": f"Intent A: {summary}"},
            {"role": "user", "content": f"Intent B: {top_memory['id']}"},
            {"role": "user", "content": f"Proposed Solution: {execution_records}"}
        ]
        
        result = chat_completion(memories_check_prompt, model="deepseek-chat", config={"temperature": 0.7})
        try:
            result = eval(result)
        except:
            result = extract_json_from_doc(result)
        
        return result["solution_sufficient"]['result'] in [True, "true"]

    def _execute_existing_records(self, execution_records):
        """Execute existing tool records"""
        for execution_record in execution_records:
            try:
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

    def _handle_new_tool_execution(self, execution_records_str, summary, plan):
        """Handle execution of new tools"""
        plan_steps = eval(plan)
        if len(plan_steps) > 1:
            all_memories = []
            for step in plan_steps:
                memories = retrieve_short_pass_memory(step["Description"])
                if not memories:
                    self.messages.append({"role": "system", "content": system_message})
                    reply = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
                    print(f"\033[92mAssistant: {reply}\033[0m")
                    continue
                all_memories.append(memories)

            for memory in all_memories:
                next_step_prompt_content = next_step_prompt(plan, memory["matches"][1]["metadata"])
        #         prompt = [{"role": "system", "content": next_step_prompt_content}]
        # # prompt.append({"role": "assistant", "content": self.messages})
        #         prompt.append({"role": "user", "content": summary})
                # plan = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.7})
                self.messages.append({"role": "system", "content": next_step_prompt_content})
                reply = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
                print(f"\033[92mAssistant: {reply}\033[0m")
        else:
            memories = retrieve_short_pass_memory(summary)
            # print(f"retrieve_short_pass_memory: {memories}")
            self.messages.append({"role": "system", "content": system_message})
            reply = chat_completion(self.messages, model="deepseek-chat", config={"temperature": 0.7})
            print(f"\033[92mAssistant: {reply}\033[0m")
            
            try:
                import json
                tool_response = json.loads(reply)
                self._execute_tool_response(tool_response, execution_records_str)
            except Exception as e:
                print(f"\033[91mError parsing JSON: {str(e)}\033[0m")

    def _execute_tool_response(self, tool_response, execution_records_str):
        """Execute tool based on response"""
        tool_name = tool_response.get("tool")
        tool_method = tool_response.get("method")
        tool_args = tool_response.get("arguments", {})
        
        if tool_name and tool_method:
            tool_record = {'tool': tool_name, 'method': tool_method, 'args': tool_args}
            print(f"toolname: {tool_name}.{tool_method} args: {tool_args}")
            
            result, execution_record = self.execute_and_record_tool(
                tool_record,
                tool_name, 
                tool_method, 
                tool_args
            )
            execution_records_str.append(execution_record)

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
    
    def _process_new_intent(self, summary):
        prompt = [{"role": "system", "content": plan_maker_prompt}]
        # prompt.append({"role": "assistant", "content": self.messages})
        prompt.append({"role": "user", "content": summary})
        plan = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.7})
        print(f"plan: {plan}")
        return plan
