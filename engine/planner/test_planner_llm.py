import sys
import os

# Get absolute path of current file
current_file_path = os.path.abspath(__file__)

# Get project root path (3 levels up)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))

# Add project root to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from engine.prompt_provider import plan_maker_prompt
from engine.llm_provider.llm import chat_completion


def create_execution_plan(intent: str) -> str:
    """Create execution plan for given intent summary"""
    prompt = [
        {"role": "system", "content": plan_maker_prompt},
        {"role": "user", "content": intent}
    ]
    plan = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.3})
    print(f"plan: {plan}")
    return plan

if __name__ == "__main__":
    """put your intent here"""
    intent = "intent"
    """you can add context to test the plan"""
    # plan = create_execution_plan(intent) + context
    plan = create_execution_plan(intent)
    print(f"plan: {plan}")

