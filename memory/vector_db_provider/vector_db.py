from memory.vector_db_provider.pinecone.pinecone import PineconeDb
from datetime import datetime

vector_db = PineconeDb(index_name="levia")


def save_memory(id: str, vector: list, metadata: dict, namespace: str):
    metadata["timestamp"] = int(datetime.now().timestamp() * 1000)
    input_embedding = {
        "id": id,
        "values": vector,
        "metadata": metadata,
    }

    vector_db.upsert([input_embedding], namespace)


def retrieve_memory(vector: list, namespace: str, top_k: int = 10):
    memories = vector_db.query(
        vector=vector,
        namespace=namespace,
        top_k=top_k,
        include_metadata=True,
        include_values=False,
    )
    return memories
