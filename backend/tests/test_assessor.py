from pathlib import Path

from PIL import Image

from cv.assessor import TomatoAssessor


IMAGE_PATH = Path(
    "tests/sample_images/tomato.jpg"
)


def main():

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Test image not found: {IMAGE_PATH}"
        )

    print("Loading image...")

    image = Image.open(
        IMAGE_PATH
    ).convert("RGB")

    # --------------------------------------------------
    # Create assessor
    # --------------------------------------------------

    assessor = TomatoAssessor()

    print("Assessor initialized.")

    # --------------------------------------------------
    # Run complete assessment
    # --------------------------------------------------

    result = assessor.assess(image)

    # --------------------------------------------------
    # Display result
    # --------------------------------------------------

    print("\nTomato Assessment")
    print("=" * 50)

    print(
        f"Disease: "
        f"{result.disease}"
    )

    print(
        f"Confidence: "
        f"{result.confidence:.2%}"
    )

    print(
        f"Class index: "
        f"{result.label_index}"
    )

    print(
        f"Affected area: "
        f"{result.affected_area_percentage:.2f}%"
    )

    print(
        f"Severity: "
        f"{result.severity_level}"
    )

    print(
        f"Leaf pixels: "
        f"{result.leaf_pixels}"
    )

    print(
        f"Affected pixels: "
        f"{result.affected_pixels}"
    )

    print(
        f"Activation threshold: "
        f"{result.activation_threshold}"
    )

    print("\nAll class scores")
    print("=" * 50)

    for disease, score in result.all_scores.items():

        print(
            f"{disease}: "
            f"{score:.2%}"
        )

    # --------------------------------------------------
    # JSON-compatible output
    # --------------------------------------------------

    print("\nJSON-compatible result")
    print("=" * 50)

    print(result.to_dict())


if __name__ == "__main__":
    main()