from pathlib import Path

import matplotlib.pyplot as plt
import cv2
from PIL import Image

from cv.gradcam import compute_gradcam
from cv.predictor import TomatoPredictor
from cv.segmentation import segment_leaf
from cv.severity import (
    estimate_severity,
    create_severity_mask,
)


IMAGE_PATH = Path("tests/sample_images/tomato.jpg")


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
    # 1. Create predictor
    # --------------------------------------------------

    predictor = TomatoPredictor()

    # --------------------------------------------------
    # 2. Prediction
    # --------------------------------------------------

    prediction = predictor.predict(image)

    print("Model loaded successfully.")

    print("\nPrediction")
    print("=" * 50)
    print(f"Disease: {prediction['disease']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"Class index: {prediction['label_index']}")

    # --------------------------------------------------
    # 3. Get the lazily-loaded model
    # --------------------------------------------------

    # TomatoPredictor loads the model internally.
    # Access the actual model through its private
    # loader rather than assuming predictor.model exists.

    model = predictor._get_model()

    # --------------------------------------------------
    # 4. Prepare model input
    # --------------------------------------------------

    input_tensor = predictor._preprocess(image)

    # --------------------------------------------------
    # 5. Generate Grad-CAM
    # --------------------------------------------------

    heatmap = compute_gradcam(
        model=model,
        input_tensor=input_tensor,
        target_class=prediction["label_index"],
    )

    print("\nGrad-CAM generated.")

    print(f"Heatmap shape: {heatmap.shape}")

    # --------------------------------------------------
    # 6. Segment leaf
    # --------------------------------------------------

    leaf_mask = segment_leaf(image)

    print("Leaf segmentation generated.")

    # --------------------------------------------------
    # 7. Estimate severity
    # --------------------------------------------------

    severity = estimate_severity(
        leaf_mask=leaf_mask,
        heatmap=heatmap,
        activation_threshold=0.5,
    )

    print("\nSeverity Estimate")
    print("=" * 50)

    print(
        f"Affected area: "
        f"{severity.affected_area_percentage:.2f}%"
    )

    print(
        f"Severity level: "
        f"{severity.severity_level}"
    )

    print(
        f"Leaf pixels: "
        f"{severity.leaf_pixels}"
    )

    print(
        f"Affected pixels: "
        f"{severity.affected_pixels}"
    )

    print(
        f"Activation threshold: "
        f"{severity.threshold}"
    )

    # --------------------------------------------------
    # 8. Create affected-area mask
    # --------------------------------------------------

    affected_mask = create_severity_mask(
        leaf_mask=leaf_mask,
        heatmap=heatmap,
        activation_threshold=0.5,
    )

    # --------------------------------------------------
    # 9. Resize Grad-CAM for display
    # --------------------------------------------------

    heatmap_display = heatmap

    if heatmap_display.shape != leaf_mask.shape:

        heatmap_display = cv2.resize(
            heatmap_display,
            (
                leaf_mask.shape[1],
                leaf_mask.shape[0],
            ),
            interpolation=cv2.INTER_LINEAR,
        )

    # --------------------------------------------------
    # 10. Display results
    # --------------------------------------------------

    plt.figure(figsize=(16, 4))

    plt.subplot(1, 4, 1)
    plt.imshow(image)
    plt.title("Original")
    plt.axis("off")

    plt.subplot(1, 4, 2)
    plt.imshow(leaf_mask, cmap="gray")
    plt.title("Leaf Mask")
    plt.axis("off")

    plt.subplot(1, 4, 3)
    plt.imshow(heatmap_display, cmap="jet")
    plt.title("Grad-CAM")
    plt.axis("off")

    plt.subplot(1, 4, 4)
    plt.imshow(affected_mask, cmap="Reds")
    plt.title(
        f"Estimated Affected Area\n"
        f"{severity.affected_area_percentage:.2f}%"
    )
    plt.axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()