from engine.prompt_provider import (
    system_message,
    messages,
    intents_system_prompt
)
from engine.llm_provider.llm import chat_completion
from memory.episodic_memory.episodic_memory import (
    store_long_pass_memory,
    retrieve_long_pass_memory
)
from engine.executor.tool_executor import execute_tool
from engine.planner.planner import create_execution_plan, check_plan_sufficiency
from engine.prompt_provider import next_step_prompt, check_tools_result_prompt
from engine.flow.evaluator.evaluator_docgen_flow import extract_json_from_doc
import json
from engine.tool_framework.tool_caller import ToolCaller
from engine.executor.chat_executor import process_existing_memories
from engine.executor.chat_executor import filter_high_score_memories


def handle_chat_flow(chat_messages: list, user_input: str, tool_caller) -> None:
    """Handle the main chat flow logic"""
    # Add user input to messages
    # chat_messages.append(messages)
    chat_messages.append({"role": "user", "content": user_input})
    
    # Get initial response
    reply_info = get_initial_response(chat_messages)
    print(f"reply_info: {reply_info}")
    
    # Handle different response types
    if reply_info["type"] == "direct_answer":
        handle_direct_answer(reply_info)
    elif reply_info["type"] == "intent_summary":
        handle_intent_summary(reply_info, chat_messages, tool_caller)

def get_initial_response(chat_messages: list) -> dict:
    """Get initial response from LLM"""
    prompt = [{"role": "system", "content": intents_system_prompt}] + chat_messages
    reply_info = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.7})
    return eval(reply_info)

def handle_direct_answer(reply_info: dict) -> None:
    """Handle direct answer type response"""
    print(f"\033[92mAssistant: {reply_info['response']}\033[0m")

def handle_intent_summary(reply_info: dict, chat_messages: list, tool_caller) -> None:
    """Handle intent summary type response"""
    summary = reply_info["summary"]
    execution_records_str = []
    
    memories = retrieve_long_pass_memory(summary)
    high_score_memories = filter_high_score_memories(memories)
    
    # if high_score_memories:
    process_existing_memories(high_score_memories, summary, execution_records_str, chat_messages, tool_caller)
    # else:
    #     process_new_intent(summary, execution_records_str, messages_history, tool_caller)
    
    # store_long_pass_memory(summary, summary, {"execution_records": execution_records_str})