
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
                    When the user inputs a sentence, respond according to the following rules:

                    1. If the input is a question or request that can be directly answered or fulfilled by a large language model, provide the answer directly.
                    2. If the input is a question or request that cannot be directly answered or fulfilled by a large language model (e.g., requires physical action, purchasing items, or other actions beyond the model's capabilities), summarize the user's intent or goal in a clear and concise manner. The summary should only describe what the user wants to achieve, without any additional output.
                    Ensure the response strictly adheres to these rules.
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
                    },
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




