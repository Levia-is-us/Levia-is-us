# engine/planner/planner.py

from engine.prompt_provider import (
    system_message
)
from engine.llm_provider.llm import chat_completion
from memory.episodic_memory.episodic_memory import (
    retrieve_short_pass_memory,
    store_long_pass_memory,
    retrieve_long_pass_memory
)
from engine.executor.tool_executor import execute_tool
from engine.planner.planner import create_execution_plan, check_plan_sufficiency
from engine.prompt_provider import next_step_prompt, check_tools_result_prompt
from engine.flow.evaluator.evaluator_docgen_flow import extract_json_from_doc
import json
from engine.tool_framework.tool_caller import ToolCaller


def process_existing_memories(high_score_memories: list, summary: str, execution_records_str: list, messages_history: list, tool_caller: ToolCaller) -> None:
    """Process existing memories from database"""
    top_memory = high_score_memories[0]
    execution_records = [eval(record) for record in top_memory["metadata"]["execution_records"]]
    
    if check_plan_sufficiency(summary, top_memory, execution_records):
        execute_existing_records(execution_records, tool_caller)
    else:
        plan = create_execution_plan(summary)
        handle_new_tool_execution(execution_records_str, summary, plan, tool_caller, messages_history)

def execute_existing_records(execution_records: list, tool_caller) -> None:
    """Execute existing tool records"""
    for record in execution_records:
        try:
            if isinstance(record, str):
                record = eval(record)
            result, _ = execute_tool(tool_caller, record["tool"], record["method"], record["args"])
            print(f"Executed tool: {record['tool']}.{record['method']}")
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error processing execution record: {str(e)}")

def process_new_intent(summary: str, execution_records_str: list, messages_history: list, tool_caller) -> None:
    """Process new intent without existing memories"""
    memories = retrieve_short_pass_memory(summary)
    messages_history.append({"role": "system", "content": system_message})
    reply = chat_completion(messages_history, model="deepseek-chat", config={"temperature": 0.7})
    print(f"\033[92mAssistant: {reply}\033[0m")
    
    try:
        tool_response = json.loads(reply)
        if isinstance(tool_response, dict):
            tool_name = tool_response.get("tool")
            tool_method = tool_response.get("method")
            tool_args = tool_response.get("arguments", {})
            
            if tool_name and tool_method:
                tool_record = {'tool': tool_name, 'method': tool_method, 'args': tool_args}
                result, execution_record = execute_tool(tool_caller, tool_name, tool_method, tool_args)
                execution_records_str.append(execution_record)
    except Exception as e:
        print(f"\033[91mError processing tool response: {str(e)}\033[0m")

def handle_new_tool_execution(execution_records_str, summary, plan, tool_caller, messages_history: list):
        """Handle execution of new tools"""
        plan_steps = eval(plan)
        if len(plan_steps) > 1:
            all_memories = []
            for step in plan_steps:
                memories = retrieve_short_pass_memory(step["Description"])
                if not memories:
                    messages_history.append({"role": "system", "content": system_message})
                    reply = chat_completion(messages_history, model="deepseek-chat", config={"temperature": 0.7})
                    print(f"\033[92mAssistant: {reply}\033[0m")
                    continue
                all_memories.append(memories["matches"][0]["metadata"]["data"])
                print(f"all_memories: {all_memories}")

            for memory in all_memories:
                next_step_prompt_content = next_step_prompt(all_memories, memory)
                prompt = [{"role": "system", "content": next_step_prompt_content}] + messages_history
                reply = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.7})
                replyJson = extract_json_from_doc(reply)
                print(f"\033[92mAssistant: {replyJson}\033[0m")
        else:
            memories = retrieve_short_pass_memory(summary)
            # print(f"retrieve_short_pass_memory: {memories}")
            messages_history.append({"role": "system", "content": system_message})
            reply = chat_completion(messages_history, model="deepseek-chat", config={"temperature": 0.7})
            print(f"\033[92mAssistant: {reply}\033[0m")
            
            try:
                import json
                try:
                    tool_response = json.loads(reply)
                except json.JSONDecodeError:
                    print(f"\033[91mInvalid JSON response: {reply}\033[0m")
                    return
                    
                if not isinstance(tool_response, dict):
                    print(f"\033[91mExpected dict response, got: {type(tool_response)}\033[0m")
                    return
                    
                tool_name = tool_response.get("tool")
                tool_method = tool_response.get("method")
                tool_args = tool_response.get("arguments", {})
                
                if not all([tool_name, tool_method]):
                    print("\033[91mMissing required tool information\033[0m")
                    return
                    
                execute_tool(tool_caller, tool_name, tool_method, tool_args)
                
            except Exception as e:
                print(f"\033[91mError processing tool response: {str(e)}\033[0m")

def filter_high_score_memories(memories: dict, threshold: float = 0) -> list:
    """Filter and sort memories by score"""
    if not memories or 'matches' not in memories:
        return []
    
    high_score_matches = [
        match for match in memories['matches']
        if match.get('score', 0) >= threshold
    ]
    
    return sorted(
        high_score_matches,
        key=lambda x: x.get('score', 0),
        reverse=True
    )