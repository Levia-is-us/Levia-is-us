
tools_description = "[{\"tool\":\"LocationTool\", \"method\": \"get_current_location\", \"desc\":\"Tool for getting location information\"}]"

system_message = f"""You are a helpful assistant with access to these tools: 

                            {tools_description}
                            Choose the appropriate tool based on the user's question. If no tool is needed, reply directly.
                            
                            IMPORTANT: When you need to use a tool, you must ONLY respond with the exact JSON object format below, nothing else:
                            {{
                                "tool": "tool-name",
                                "method": "method-name",
                                "desc": "description of the tool execution",
                                "arguments": {{
                                    "argument-name": "value"
                                }}
                            }}
                            
                            After receiving a tool's response:
                            1. Transform the raw data into a natural, conversational response
                            2. Keep responses concise but informative
                            3. Focus on the most relevant information
                            4. Use appropriate context from the user's question
                            5. Avoid simply repeating the raw data
                            
                            Please use only the tools that are explicitly defined above."""

intents_system_prompt = """
                        When the user inputs a sentence, respond in the following JSON format:

                        1. If the input is a question or request that can be solved directly by a large language model, output:
                        {
                            "type": "direct_answer",
                            "response": "[Your answer here]"
                        }
                            make sure the response does not directly answer can not solve the problem.
                        2. If the input is a question or request that cannot be directly answered or fulfilled by a large language model (e.g., requires physical action, purchasing items, or actions beyond the model's capabilities), output a summary as short as possible:
                        {
                            "type": "intent_summary",
                            "summary": "[Summarize the user's intent or goal here]"
                        }
                        Ensure all responses strictly follow this JSON structure for consistent processing.
                    """

check_plan_fittable_prompt = """
                    You are an expert in natural language understanding and semantic analysis. Your task is to compare two intents or evaluate whether a proposed solution fulfills a given intent.

                    Input:

                    1. Intent A/Requirement Description: {Intent A/Requirement Description}
                    2. Intent B and Proposed Solution: {Intent B/Proposed Solution}
                    Analyze the relationship between the two inputs and output your findings in the following structured JSON format:
                    {
                    "intent_match": {
                        "result": true/false,
                        "reason": "Brief explanation of whether Intent A and Intent B match or not."
                    }
                    "solution_sufficient": {
                        "result": true/false,
                        "reason": "Brief explanation of whether the proposed solution satisfies Intent A."
                    }
                    }          
                    """

messages = [
    {
        "role": "system",
        "content": intents_system_prompt
    }
]

def next_step_prompt(workflow, current_step):
    next_step_prompt = f"""
                        You are provided with a workflow consisting of multiple tools. Each tool has a name, method, required arguments, optional arguments, and an expected output. The workflow executes tools sequentially. The input for the workflow may consist of natural language, structured data, key-value pairs, or a mix of these formats. Your task is to evaluate whether the input and the outputs from previously executed tools provide sufficient information to proceed with each tool in the workflow.

                        Here is the workflow: {workflow}
                        [{
                            "tool": "BBC_news",
                            "method": "find_news",
                            "requirement_arguments": [],
                            "optional_arguments": [
                                {"argument-name": "date"},
                                {"argument-name": "type_of_news"},
                                {"argument-name": "key_words"}
                            ],
                            "output": [{"time":"datetime","news":"news"},{"time":"datetime","news":"news"},{"time":"datetime","news":"news"}]
                        }, {
                            "tool": "tweet_tool",
                            "method": "send_tweet",
                            "requirement_arguments": [
                                {"argument-name": "account"}, {"argument-name": "password"}, {"argument-name": "tweets"}
                            ],
                            "optional_arguments": [
                                {"argument-name": "time"}
                            ],
                            "output": "output"
                        }]

                        next step is : {current_step}
                        {
                            "tool": "BBC_news",
                            "method": "find_news",
                            "requirement_arguments": [],
                            "optional_arguments": [
                                {"argument-name": "date"},
                                {"argument-name": "type_of_news"},
                                {"argument-name": "key_words"}
                            ],
                            "output": "[{"time":"datetime","news":"news"},{"time":"datetime","news":"news"},{"time":"datetime","news":"news"}]
                        }

                        For each step in the following workflow:

                        1. Extract Arguments: Identify all required and optional arguments provided from the input and previous outputs.

                        2. Validation:

                        - Confirm if all required arguments for the current tool are satisfied.
                        - Evaluate if any optional arguments are needed and determine if they can be derived from the input or previous outputs.

                        Action:

                        If all required arguments are present and no critical information is missing, only output a json fit the arguments of next format, do not output anthing else:
                        {
                            "step": "<current step number>",
                            "can_proceed": true,
                            "extracted_arguments": {
                                "required_arguments": {
                                    "<argument-name>": "<value>"
                                },
                                "optional_arguments": {
                                    "<argument-name>": "<value>"
                                }
                            }
                        }

                        If the step cannot proceed, output the following format with details of missing information:
                        Output your results in the following only JSON format for programmatic processing:
                        [{
                            "step": "<current step number>",
                            "can_proceed": <true/false>,
                            "missing_required_arguments": [<list of missing required arguments>],
                            "needed_optional_arguments": [<list of optional arguments that are required>],
                            "remarks": "<natural language explanation if applicable>"
                        }]
                        """
    return next_step_prompt

def check_tools_result_prompt(tool_excution, tool_output):
    messages = []
    prompt = f"""Analyze the tool's output and generate a JSON response with the following structure:

                                    - status: The execution status of the tool, categorized as one of the following:
                                    1. success: Tool executed successfully, including errors caused by incorrect parameters.
                                    2. tool_error: Tool execution failed due to a code-related error.
                                    3. unknown_error: Unable to determine the status from the output.
                                    - error_reason: A detailed explanation of the status and, if applicable, the specific cause of the error.
                                    Ensure the JSON response is clear, structured, and easy to parse.
                                    """
    messages.append({"role": "system", "content": prompt})
    messages.append({"role": "user", "content": f"tool_excution: {tool_excution}"})
    messages.append({"role": "user", "content": f"tool_output: {tool_output}"})
    return messages

