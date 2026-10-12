import asyncio

from nlp.responder import AdvisoryResponder


class FakeRetriever:
    """Fake RAG retriever used for unit testing."""

    def __init__(self):
        self.last_query = None
        self.last_disease = None
        self.last_top_k = None

    async def retrieve(
        self,
        query: str,
        disease: str | None = None,
        top_k: int = 5,
    ):
        self.last_query = query
        self.last_disease = disease
        self.last_top_k = top_k

        return [
            {
                "id": 1,
                "content": (
                    "Early blight commonly causes dark lesions "
                    "on older tomato leaves."
                ),
                "disease_tag": "Early Blight",
                "title": "KILIMO Tomato Disease Knowledge Base",
                "source": "KILIMO internal knowledge base",
                "similarity": 0.82,
            }
        ]


def test_responder_uses_rag_context(monkeypatch):
    retriever = FakeRetriever()

    responder = AdvisoryResponder(
        retriever=retriever
    )

    def fake_generate(model, prompt):
        assert "Early Blight" in prompt
        assert "dark lesions" in prompt

        # Current prompt headings
        assert (
            "Retrieved agricultural reference material:"
            in prompt
        )

        assert (
            "Current assessment:"
            in prompt
        )

        return "The system detected Early Blight."

    monkeypatch.setattr(
        responder,
        "_generate_sync",
        fake_generate,
    )

    advisory = {
        "disease": "Early Blight",
        "confidence": 0.95,
        "severity": "Moderate",
        "affected_area_percentage": 18.5,
        "description": (
            "A fungal disease that can affect tomato foliage."
        ),
        "symptoms": [
            "Dark spots on older leaves."
        ],
        "recommended_actions": [
            "Remove affected leaves.",
            "Improve airflow."
        ],
        "prevention": [
            "Avoid prolonged leaf wetness."
        ],
        "confidence_message": (
            "The model is highly confident in this prediction."
        ),
        "urgency": "Medium",
    }

    result = asyncio.run(
        responder.generate(advisory)
    )

    assert (
        result
        == "The system detected Early Blight."
    )

    assert (
        retriever.last_disease
        == "Early Blight"
    )

    # Current responder retrieves up to 4 chunks.
    assert retriever.last_top_k == 4

    assert retriever.last_query is not None

    # Current RAG query includes useful assessment context.
    assert "Early Blight" in retriever.last_query
    assert "Moderate" in retriever.last_query


def test_responder_uses_farmer_question_for_rag(
    monkeypatch,
):
    retriever = FakeRetriever()

    responder = AdvisoryResponder(
        retriever=retriever
    )

    def fake_generate(model, prompt):
        assert (
            "How can I prevent it from spreading?"
            in prompt
        )

        return (
            "Follow the prevention guidance provided."
        )

    monkeypatch.setattr(
        responder,
        "_generate_sync",
        fake_generate,
    )

    advisory = {
        "disease": "Early Blight",
        "confidence": 0.91,
        "severity": "Low",
        "affected_area_percentage": 5.0,
        "description": "Tomato disease.",
        "symptoms": [],
        "recommended_actions": [],
        "prevention": [],
        "confidence_message": "High confidence.",
        "urgency": "Low",
    }

    result = asyncio.run(
        responder.generate(
            advisory,
            farmer_query=(
                "How can I prevent it from spreading?"
            ),
        )
    )

    assert (
        result
        == "Follow the prevention guidance provided."
    )

    assert retriever.last_query is not None

    # The current RAG query intentionally includes
    # assessment context as well as the farmer's question.
    assert "Early Blight" in retriever.last_query
    assert "Low" in retriever.last_query

    assert (
        "How can I prevent it from spreading?"
        in retriever.last_query
    )

    assert (
        retriever.last_disease
        == "Early Blight"
    )


def test_rag_query_is_generated_when_no_question():
    advisory = {
        "disease": "Late Blight",
        "confidence": 0.94,
        "severity": "High",
        "symptoms": [
            "Dark lesions",
            "Rapid spread",
        ],
    }

    query = AdvisoryResponder._build_rag_query(
        advisory=advisory,
        farmer_query="",
        conversation_history=None,
        has_assessment=True,
    )

    assert "Late Blight" in query
    assert "High" in query
    assert "Symptoms" in query
    assert "management" in query
    assert "prevention" in query