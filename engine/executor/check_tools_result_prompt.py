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

plan_maker_prompt = """
                    Based on the given input, identify and list only the tasks that cannot be completed by an LLM. For each task, include:

                    1. Name: A clear title for the task.
                    2. Description: A concise description of what needs to be done for this task.
                    Input:
                    {Provide the user input here}

                    Context:
                    {Provide relevant background information here}

                    Output:
                    Provide the results in the following format without any other text:
                    [
                    {
                        "Name": "Task 1 Name",
                        "Description": "Explanation of what needs to be done for this task."
                    },
                    {
                        "Name": "Task 2 Name",
                        "Description": "Explanation of what needs to be done for this task"
                    },
                    ...
                    ]
                    """