import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict

class VectorIndex:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.chunks: List[Dict[str, any]] = []
        self.tfidf_matrix = None

    def fit(self, chunks: List[Dict[str, any]]):
        self.chunks = chunks
        if not chunks:
            self.tfidf_matrix = None
            return

        corpus = [c["text"] for c in chunks]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, any], float]]:
        if self.tfidf_matrix is None or not self.chunks:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Sort indices by descending score
        top_indices = similarities.argsort()[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.05:  # Relevance threshold
                results.append((self.chunks[idx], score))
        return results

    def get_chunk_vector(self, text: str) -> List[float]:
        """
        Returns a normalized vector array suitable for storing in MySQL knowledge_chunks JSON column.
        """
        if self.tfidf_matrix is None:
            return []
        vec = self.vectorizer.transform([text]).toarray()[0]
        # Return non-zero values or top 10 dimensions for compact storage
        return [round(float(v), 4) for v in vec[:20]]
