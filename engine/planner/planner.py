from engine.prompt_provider import plan_maker_prompt
from engine.llm_provider.llm import chat_completion
from engine.flow.evaluator.evaluator_docgen_flow import extract_json_from_doc
from engine.prompt_provider import  check_plan_fittable_prompt

def create_execution_plan(summary: str) -> str:
    """Create execution plan for given intent summary"""
    prompt = [
        {"role": "system", "content": plan_maker_prompt},
        {"role": "user", "content": summary}
    ]
    plan = chat_completion(prompt, model="deepseek-chat", config={"temperature": 0.7})
    print(f"plan: {plan}")
    return plan

def check_plan_sufficiency(summary: str, plan: str, execution_records: list) -> bool:
    """Check if existing plan is sufficient for current intent"""
    memories_check_prompt = [
        {"role": "system", "content": check_plan_fittable_prompt},
        {"role": "user", "content": f"Intent A: {summary}"},
        {"role": "user", "content": f"Intent B: {plan}"},
        {"role": "user", "content": f"Proposed Solution: {execution_records}"}
    ]
    
    result = chat_completion(memories_check_prompt, model="deepseek-chat", 
                           config={"temperature": 0.7})
    try:
        result = eval(result)
    except:
        result = extract_json_from_doc(result)
    
    return result["solution_sufficient"]['result'] in [True, "true"]