import json

from engine.llm_provider.openai.openai import (
    chat_completion_openai,
    generate_embeddings,
)
from engine.llm_provider.claude.claude import chat_completion_anthropic
from engine.llm_provider.deepseek.deepseek import chat_completion_deepseek


# Cache models configuration
_models = None
_default_model = "deepseek-reasoner"


def _load_models():
    """Load models configuration from JSON file if not already loaded"""
    global _models
    if _models is None:
        with open("engine/llm_provider/models.json", "r") as f:
            models_list = json.load(f)
            _models = {model["model"]: model for model in models_list}
    return _models


def create_chat_completion(system_prompt, prompt, model=_default_model, config={}):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    return chat_completion(messages, model, config)


def create_embedding(text, model="text-embedding", config={}):
    """
    Generate embeddings using the specified model.

    Parameters:
    - text: Text to generate embeddings for
    - model: Model identifier to use (default: "text-embedding")
    - config: Additional configuration parameters to pass to the underlying API

    Returns:
    - list: The generated embedding vector
    """
    models = _load_models()

    if models[model]["source"] == "openai":
        return generate_embeddings(text, model=model, version=models[model]["version"])

    raise ValueError(f"Model {model} does not support embeddings")


def chat_completion(messages, model=_default_model, config={}):
    """
    Generate chat completion using either OpenAI or Anthropic models.

    Parameters:
    - messages: List of messages to simulate a conversation.
      Each message is a dictionary containing:
      - role: The role of the message sender ("system", "user", or "assistant")
      - content: The message content (string or list of content objects)
    - model: Model identifier to use (default: "gpt-3.5-turbo")
    - config: Additional configuration parameters to pass to the underlying API

    Returns:
    - str: The model's reply message content

    The function reads model configurations from a JSON file that specifies:
    - source: The API provider ("openai" or "anthropic")
    - version: The specific model version to use

    For Anthropic models, messages are automatically converted to the required format
    where content is wrapped in a list of content objects with type and text fields.
    """
    models = _load_models()

    if models[model]["source"] == "openai":
        return chat_completion_openai(
            messages, model=model, version=models[model]["version"], config=config
        )
    elif models[model]["source"] == "deepseek":
        return chat_completion_deepseek(messages, model=model, config=config)
    elif models[model]["source"] == "anthropic":
        # convert messages to anthropic format
        anthropic_messages = []
        for message in messages:
            message_type = type(message["content"])
            if message_type == str:
                anthropic_messages.append(
                    {
                        "role": message["role"],
                        "content": [{"type": "text", "text": message["content"]}],
                    }
                )
            else:
                anthropic_messages.append(
                    {
                        "role": message["role"],
                        "content": [
                            {"type": "text", "text": json.dumps(message["content"])}
                        ],
                    }
                )

        return chat_completion_anthropic(
            anthropic_messages, model=models[model]["version"], config=config
        )

    return chat_completion_openai(messages)