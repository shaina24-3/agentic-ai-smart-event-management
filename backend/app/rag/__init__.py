from typing import List, Tuple
from .retriever import retriever
from .pipeline import answer_policy_question

class RealRAGBridge:
    def retrieve(self, query: str, top_k: int = 1) -> List[Tuple[str, float]]:
        results = retriever.retrieve(query, top_k=top_k)
        return [(r["text"], float(r.get("score", 0.9))) for r in results]

rag_engine = RealRAGBridge()

__all__ = ["retriever", "answer_policy_question", "rag_engine"]
