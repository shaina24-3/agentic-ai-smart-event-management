from typing import List, Dict, Optional
from .loader import load_documents
from .chunker import create_chunks_from_documents
from .embeddings import VectorIndex

class KnowledgeRetriever:
    def __init__(self):
        self.index = VectorIndex()
        self.documents = []
        self.chunks = []
        self.reload()

    def reload(self):
        """
        Reloads all documents from documents folder and reindexes chunks.
        """
        self.documents = load_documents()
        self.chunks = create_chunks_from_documents(self.documents)
        self.index.fit(self.chunks)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, any]]:
        """
        Retrieves the top-k most relevant policy chunks with similarity scores.
        """
        raw_results = self.index.search(query, top_k=top_k)
        formatted = []
        for chunk, score in raw_results:
            formatted.append({
                "doc_title": chunk["doc_title"],
                "file_name": chunk["file_name"],
                "text": chunk["text"],
                "score": score
            })
        return formatted

# Singleton retriever instance
retriever = KnowledgeRetriever()
