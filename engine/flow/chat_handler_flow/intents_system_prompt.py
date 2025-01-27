intents_system_prompt = f"""
                        When the user inputs a sentence, respond in the following JSON format:

                        1. If the input is a question or request that can be solved directly by a large language model, output:
                        {{
                            "type": "direct_answer",
                            "response": "[Your answer here]"
                        }}
                            make sure the response does not directly answer can not solve the problem.
                        2. If the input is a question or request that cannot be directly answered or fulfilled by a large language model (e.g., requires physical action, purchasing items, or actions beyond the model's capabilities), output a summary as short as possible:
                        {{
                            "type": "intent_summary",
                            "summary": "[Summarize the user's intent or goal here]"
                        }}
                        Ensure all responses strictly follow this JSON structure for consistent processing.
                    """