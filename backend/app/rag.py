from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple

POLICY_DOCUMENTS = [
    "Cancellation Policy: Participants may cancel their event registrations up to 24 hours before the scheduled start time without any penalty.",
    "Event Capacity Rules: Events strictly adhere to venue room capacities. Once maximum capacity is reached, new registrations are blocked automatically.",
    "Venue Policy: Venues are allocated based on event requirements. Only one event can occupy a venue at any given time slot.",
    "Attendance Policy: Registered attendees must check in with their registered email address at least 15 minutes before the event begins.",
    "FAQ: Organizers with ADMIN permissions can create, update, or cancel events, while participants can register and manage their reservations."
]

class LocalRAG:
    def __init__(self, docs: List[str]):
        self.docs = docs
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.doc_vectors = self.vectorizer.fit_transform(self.docs)

    def retrieve(self, query: str, top_k: int = 1) -> List[Tuple[str, float]]:
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.doc_vectors).flatten()
        best_indices = similarities.argsort()[::-1][:top_k]
        return [(self.docs[idx], float(similarities[idx])) for idx in best_indices if similarities[idx] > 0.05]

rag_engine = LocalRAG(POLICY_DOCUMENTS)
