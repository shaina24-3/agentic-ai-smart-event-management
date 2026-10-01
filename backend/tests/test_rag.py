from app.rag import rag_engine


def test_rag_cancellation_policy():
    results = rag_engine.retrieve(
        "Can I cancel my event registration?"
    )

    assert len(results) > 0
    document, score = results[0]

    assert "Cancellation Policy" in document
    assert score > 0.05


def test_rag_capacity_policy():
    results = rag_engine.retrieve(
        "What happens when an event reaches maximum capacity?"
    )

    assert len(results) > 0
    document, score = results[0]

    assert "Event Capacity Rules" in document
    assert score > 0.05


def test_rag_venue_policy():
    results = rag_engine.retrieve(
        "Can two events use the same venue at the same time?"
    )

    assert len(results) > 0
    document, score = results[0]

    assert "Venue Policy" in document
    assert score > 0.05


def test_rag_attendance_policy():
    results = rag_engine.retrieve(
        "When should registered attendees check in?"
    )

    assert len(results) > 0
    document, score = results[0]

    assert "Attendance Policy" in document
    assert score > 0.05


def test_rag_faq():
    results = rag_engine.retrieve(
        "Who can create and cancel events?"
    )

    assert len(results) > 0
    document, score = results[0]

    assert "FAQ" in document
    assert score > 0.05