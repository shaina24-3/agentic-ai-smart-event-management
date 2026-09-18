import json
import logging
import math
import os
from typing import List, Tuple

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from .models import KnowledgeChunk


# ---------------------------------------------------------
# Environment / Logging
# ---------------------------------------------------------

load_dotenv()

logger = logging.getLogger(__name__)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Add it to backend/.env"
    )


# ---------------------------------------------------------
# Gemini Client
# ---------------------------------------------------------

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# Models
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"


# ---------------------------------------------------------
# Create Embedding
# ---------------------------------------------------------

def create_embedding(text: str) -> List[float]:
    """
    Convert text into a Gemini embedding vector.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot create an embedding for empty text."
        )

    try:

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini returned no embeddings."
            )

        embedding = response.embeddings[0].values

        if not embedding:
            raise RuntimeError(
                "Gemini returned an empty embedding."
            )

        return list(embedding)

    except Exception as error:

        logger.exception(
            "Failed to create Gemini embedding"
        )

        raise RuntimeError(
            f"Embedding generation failed: {error}"
        ) from error


# ---------------------------------------------------------
# Cosine Similarity
# ---------------------------------------------------------

def cosine_similarity(
    vector_a: List[float],
    vector_b: List[float]
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        logger.warning(
            "Embedding dimension mismatch: %s vs %s",
            len(vector_a),
            len(vector_b)
        )
        return 0.0

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# ---------------------------------------------------------
# Retrieve Relevant Knowledge Chunks
# ---------------------------------------------------------

def retrieve_relevant_chunks(
    db: Session,
    query: str,
    top_k: int = 3,
    similarity_threshold: float = 0.20
) -> List[Tuple[KnowledgeChunk, float]]:
    """
    Retrieve the most relevant knowledge chunks
    using Gemini embeddings and cosine similarity.
    """

    if not query or not query.strip():
        return []

    # Create embedding for the user's question
    query_embedding = create_embedding(query)

    # Get knowledge chunks that have embeddings
    chunks = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.embedding.isnot(None)
        )
        .all()
    )

    if not chunks:
        logger.warning(
            "No embedded knowledge chunks found."
        )
        return []

    scored_chunks = []

    for chunk in chunks:

        try:

            stored_embedding = chunk.embedding

            # SQLAlchemy/MySQL JSON may already return a list.
            # This also handles a JSON string safely.
            if isinstance(
                stored_embedding,
                str
            ):
                stored_embedding = json.loads(
                    stored_embedding
                )

            if not isinstance(
                stored_embedding,
                list
            ):
                logger.warning(
                    "Invalid embedding for chunk %s",
                    chunk.id
                )
                continue

            score = cosine_similarity(
                query_embedding,
                stored_embedding
            )

            if score >= similarity_threshold:

                scored_chunks.append(
                    (chunk, score)
                )

        except Exception as error:

            logger.warning(
                "Could not process chunk %s: %s",
                chunk.id,
                error
            )

    # Highest similarity first
    scored_chunks.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return scored_chunks[:top_k]


# ---------------------------------------------------------
# Generate Grounded Answer
# ---------------------------------------------------------

def generate_grounded_answer(
    query: str,
    retrieved_chunks: List[Tuple[KnowledgeChunk, float]]
) -> str:
    """
    Generate an answer using ONLY the retrieved
    knowledge-base information.
    """

    if not retrieved_chunks:

        return (
            "I couldn't find enough information about "
            "that in the event management knowledge base."
        )

    # Build context from retrieved chunks
    context_parts = []

    for index, (chunk, score) in enumerate(
        retrieved_chunks,
        start=1
    ):

        context_parts.append(
            f"Knowledge Source {index} "
            f"(relevance: {score:.3f}):\n"
            f"{chunk.chunk_text}"
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are the AI assistant for a Smart Event Management System.

Answer the user's question using ONLY the knowledge
provided in the knowledge base below.

Important rules:

1. Do not invent policies, rules, dates, capacities,
   penalties, procedures, or other information.

2. If the knowledge base does not contain enough
   information to answer the question, clearly say
   that the information is not available in the
   knowledge base.

3. Do not use outside knowledge.

4. Give a concise and natural answer.

5. If the question asks about a policy, explain the
   relevant policy directly.

Knowledge Base:
----------------
{context}
----------------

User Question:
{query}

Answer:
"""

    try:

        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text.strip()

    except Exception as error:

        logger.exception(
            "Failed to generate grounded answer"
        )

        raise RuntimeError(
            f"Answer generation failed: {error}"
        ) from error


# ---------------------------------------------------------
# Complete RAG Pipeline
# ---------------------------------------------------------

def answer_with_rag(
    db: Session,
    query: str,
    top_k: int = 3
) -> str:
    """
    Complete RAG pipeline:

    User query
        ↓
    Query embedding
        ↓
    Similarity search
        ↓
    Top-K knowledge chunks
        ↓
    Gemini grounded generation
        ↓
    Final answer
    """

    if not query or not query.strip():
        return (
            "Please provide a question about "
            "the event management system."
        )

    retrieved_chunks = retrieve_relevant_chunks(
        db=db,
        query=query,
        top_k=top_k
    )

    logger.info(
        "Retrieved %s chunks for query: %s",
        len(retrieved_chunks),
        query
    )

    return generate_grounded_answer(
        query=query,
        retrieved_chunks=retrieved_chunks
    )