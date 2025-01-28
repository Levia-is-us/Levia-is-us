import sys
import os

# Get absolute path of current file
current_file_path = os.path.abspath(__file__)

# Get project root path (3 levels up)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))

# Add project root to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from engine.prompt_provider import (
    intents_system_prompt
)
from engine.llm_provider.llm import chat_completion
from engine.flow.evaluator.evaluator_docgen_flow import extract_json_from_doc


def get_initial_response(chat_messages: list) -> dict:
    """Get initial response from LLM"""
    prompt = [{"role": "system", "content": intents_system_prompt}] + chat_messages
    reply_info = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.3})
    return extract_json_from_doc(reply_info)

def main():
    chat_messages = input("Enter your message: ")
    get_initial_response(chat_messages)

if __name__ == "__main__":
    main()
