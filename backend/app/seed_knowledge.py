from .database import SessionLocal
from .models import KnowledgeDocument, KnowledgeChunk


KNOWLEDGE_DATA = [
    {
        "title": "Event Cancellation Policy",
        "chunks": [
            "Participants may cancel their event registrations up to 24 hours before the scheduled start time without any penalty.",
            "Organizers can reschedule or cancel events, and registered users will be notified."
        ]
    },
    {
        "title": "Registration & Attendance Policy",
        "chunks": [
            "Event registration is capped based on the venue capacity. Registrations are handled on a first-come-first-served basis, and duplicate registrations are blocked."
        ]
    },
    {
        "title": "FAQ",
        "chunks": [
            "The AI assistant can help users find events, understand event policies, and manage their event registrations."
        ]
    }
]


def seed_knowledge():
    db = SessionLocal()

    try:
        # Prevent duplicate seeding
        existing = db.query(KnowledgeDocument).count()

        if existing > 0:
            print("Knowledge base already contains documents.")
            return

        for document_data in KNOWLEDGE_DATA:

            document = KnowledgeDocument(
                title=document_data["title"]
            )

            db.add(document)
            db.flush()

            for index, text in enumerate(document_data["chunks"]):

                chunk = KnowledgeChunk(
                    document_id=document.id,
                    chunk_text=text,
                    chunk_index=index
                )

                db.add(chunk)

        db.commit()

        print("Knowledge base seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_knowledge()