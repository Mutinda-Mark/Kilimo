from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

from cv.segmentation import (
    segment_leaf,
    calculate_leaf_percentage,
    create_mask_overlay,
)


# Change this to any tomato image you want to test
IMAGE_PATH = Path("tests/sample_images/tomato.jpg")


def main():
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Test image not found: {IMAGE_PATH}"
        )

    image = Image.open(IMAGE_PATH).convert("RGB")

    print("Image loaded successfully.")
    print(f"Original size: {image.size}")

    # Generate leaf mask
    mask = segment_leaf(image)

    print("\nLeaf Segmentation")
    print("=" * 50)

    print(f"Mask shape: {mask.shape}")
    print(f"Mask data type: {mask.dtype}")

    leaf_percentage = calculate_leaf_percentage(mask)

    print(f"Estimated leaf coverage: {leaf_percentage:.2f}%")

    # Create visualization
    overlay = create_mask_overlay(image, mask)

    # Display results
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 3, 1)
    plt.imshow(image)
    plt.title("Original")
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.imshow(mask, cmap="gray")
    plt.title("Leaf Mask")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.imshow(overlay)
    plt.title("Leaf Segmentation")
    plt.axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()