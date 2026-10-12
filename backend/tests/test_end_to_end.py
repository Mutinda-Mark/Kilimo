import asyncio
from pathlib import Path

from PIL import Image

from cv.assessor import TomatoAssessor
from nlp.advisory import AdvisoryEngine
from nlp.responder import AdvisoryResponder


# Change this if you want to test another image.
SAMPLE_IMAGE = (
    Path(__file__).parent
    / "sample_images"
    / "tomato.jpg"
)


async def run_end_to_end_test():
    print("\n" + "=" * 70)
    print("KILIMO END-TO-END TEST")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Check image
    # ---------------------------------------------------------------

    if not SAMPLE_IMAGE.exists():
        raise FileNotFoundError(
            f"Test image not found: {SAMPLE_IMAGE}"
        )

    print(f"\nImage: {SAMPLE_IMAGE}")

    image = Image.open(SAMPLE_IMAGE).convert("RGB")

    print(
        f"Image size: {image.size}"
    )

    # ---------------------------------------------------------------
    # 2. Computer vision assessment
    # ---------------------------------------------------------------

    print("\n[1/4] Running computer vision assessment...")

    assessor = TomatoAssessor()

    assessment = assessor.assess(image)

    assessment_data = assessment.to_dict()

    print(
        f"Disease: {assessment_data['disease']}"
    )

    print(
        f"Confidence: "
        f"{assessment_data['confidence']:.2%}"
    )

    print(
        f"Severity: "
        f"{assessment_data['severity_level']}"
    )

    print(
        f"Affected area: "
        f"{assessment_data['affected_area_percentage']:.2f}%"
    )

    # ---------------------------------------------------------------
    # 3. Structured advisory
    # ---------------------------------------------------------------

    print("\n[2/4] Generating structured advisory...")

    advisory_engine = AdvisoryEngine()

    advisory = advisory_engine.generate(
        assessment_data
    )

    print(
        f"Advisory disease: "
        f"{advisory['disease']}"
    )

    print(
        f"Urgency: "
        f"{advisory['urgency']}"
    )

    # ---------------------------------------------------------------
    # 4. RAG + Gemini
    # ---------------------------------------------------------------

    print("\n[3/4] Running RAG retrieval + Gemini...")

    responder = AdvisoryResponder()

    response = await responder.generate(
        advisory=advisory
    )

    print("\n[4/4] FINAL FARMER RESPONSE")
    print("-" * 70)

    print(response)

    print("-" * 70)

    print("\nEND-TO-END TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(
        run_end_to_end_test()
    )