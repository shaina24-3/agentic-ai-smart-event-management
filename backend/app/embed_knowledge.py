from .database import SessionLocal
from .models import KnowledgeChunk
from .rag import create_embedding


def embed_all_chunks():
    db = SessionLocal()

    try:
        chunks = db.query(KnowledgeChunk).all()

        print(f"Found {len(chunks)} knowledge chunks.")

        for chunk in chunks:

            print(f"Embedding chunk {chunk.id}...")

            chunk.embedding = create_embedding(
                chunk.chunk_text
            )

        db.commit()

        print("All knowledge chunks embedded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    embed_all_chunks()