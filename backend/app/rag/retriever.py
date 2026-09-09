import math
import re
from typing import List, Dict
from app.rag.loader import DocumentLoader
from app.rag.chunker import DocumentChunker

class KnowledgeRetriever:
    _instance = None
    
    def __init__(self, docs_dir: str = "documents"):
        self.docs_dir = docs_dir
        self.chunks: List[Dict[str, str]] = []
        self._load_and_index()

    @classmethod
    def get_instance(cls, docs_dir: str = "documents"):
        if cls._instance is None:
            cls._instance = cls(docs_dir)
        return cls._instance

    def _load_and_index(self):
        docs = DocumentLoader.load_documents_from_dir(self.docs_dir)
        self.chunks = []
        for doc in docs:
            self.chunks.extend(DocumentChunker.chunk_document(doc))

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, any]]:
        if not self.chunks:
            self._load_and_index()
            
        q_tokens = set(self._tokenize(query))
        if not q_tokens:
            return []

        scored_chunks = []
        for item in self.chunks:
            chunk_tokens = self._tokenize(item["chunk"])
            if not chunk_tokens:
                continue
            
            matches = sum(1 for t in q_tokens if t in chunk_tokens)
            score = (matches * 2.0) / (math.sqrt(len(chunk_tokens)) + 1.0)
            if query.lower() in item["chunk"].lower():
                score += 3.0
                
            if score > 0:
                scored_chunks.append({
                    "source": item["source"],
                    "content": item["chunk"],
                    "score": round(score, 3)
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
