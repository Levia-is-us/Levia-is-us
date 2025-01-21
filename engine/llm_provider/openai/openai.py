from openai import AzureOpenAI

import os

api_key = os.getenv("OPENAI_API_KEY")
host = os.getenv("OPENAI_BASE_URL")


def chat_completion_openai(
    messages, model="gpt-35-turbo-16k", version="2024-05-01-preview", config={}
):
    """
    Generate chat completion using OpenAI API.

    Parameters:
    - messages: List of messages to simulate a conversation
      Each message is a dictionary containing the role ("user" or "system" or "assistant") and content ("content").

    Returns:
    - model reply message content
    """
    try:
        client = AzureOpenAI(
            azure_endpoint=host,
            api_key=api_key,
            api_version=version,
        )
        # Remove default parameters that might conflict with config
        completion_params = {
            "model": model,
            "messages": messages,
            "max_tokens": 800,
            "stream": False,
        }
        # Update with any additional config parameters
        completion_params.update(config)

        completion = client.chat.completions.create(**completion_params)

        # Extract the model reply
        return completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def generate_embeddings(text, model="text-embedding", version="2023-05-15"):
    client = AzureOpenAI(
        api_key=api_key,
        api_version=version,
        azure_endpoint=host,
        max_retries=0,
    )
    data = client.embeddings.create(input=[text], model=model)
    return data.data[0].embedding
