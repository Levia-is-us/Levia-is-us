from memory.vector_db_provider.vector_db import save_memory, retrieve_memory
from engine.llm_provider.llm import create_embedding

short_pass_namespace = "short_pass"
long_pass_namespace = "long_pass"


def store_short_pass_memory(
    id: str,
    memory: str,
    metadata: dict,
    namespace: str = short_pass_namespace,
    uid: str = "levia",
):
    try:
        metadata["uid"] = uid
        for key, value in metadata.items():
            if isinstance(value, dict):
                metadata[key] = str(value)
        embedding = create_embedding(memory)
        save_memory(id, embedding, metadata, namespace)
    except Exception as e:
        print(f"\033[91mError storing short pass memory: {str(e)}\033[0m")


def retrieve_short_pass_memory(
    query: str, namespace: str = short_pass_namespace, uid: str = "levia"
):
    embedding = create_embedding(query)
    memories = retrieve_memory(embedding, namespace)
    return memories


def store_long_pass_memory(
    id: str,
    memory: str,
    metadata: dict,
    namespace: str = long_pass_namespace,
    uid: str = "levia",
):
    try:
        metadata["uid"] = uid
        for key, value in metadata.items():
            if isinstance(value, dict):
                metadata[key] = str(value)
        embedding = create_embedding(memory)
        save_memory(id, embedding, metadata, namespace)
    except Exception as e:
        print(f"\033[91mError storing long pass memory: {str(e)}\033[0m")


def retrieve_long_pass_memory(
    query: str, namespace: str = long_pass_namespace, uid: str = "levia"
):

    embedding = create_embedding(query)
    memories = retrieve_memory(embedding, namespace)
    return memories
