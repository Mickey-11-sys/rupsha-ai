
import chromadb
import os
import config
from embeddings import get_embedding

class VectorMemory:
    """
    RUPSHA's semantic memory.
    NEW way: Search for similar MEANING.
    """

    def __init__(self, persist_dir=config.VECTOR_DB_PATH):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)

        self.collection = self.client.get_or_create_collection(
            name="rupsha_memories",
            metadata={"hnsw:space": "cosine"}
        )

    def add(self, memory_id, text, metadata=None):
        if metadata is None:
            metadata = {}

        embedding = get_embedding(text)

        self.collection.add(
            ids=[memory_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        print(f"VectorMemory: Saved '{text[:50]}...'")

    def search(self, query_text, n_results=5):
        if not query_text:
            return []

        query_embedding = get_embedding(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        memories = []
        for i in range(len(results["ids"][0])):
            memories.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return memories

    def delete(self, memory_id):
        self.collection.delete(ids=[memory_id])

    def count(self):
        return self.collection.count()
