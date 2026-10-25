"""
Prepare the KILIMO tomato-subject validation dataset.

The resulting dataset contains two classes:

    supported_tomato_leaf
    unsupported_image

Supported examples are collected recursively from the existing
tomato disease dataset.

Unsupported examples are collected recursively from a separate
source directory containing other leaves, other plant material,
and unrelated real-world images.

The script creates deterministic train/validation/test splits.

IMPORTANT:
The held-out test split should not be used for threshold selection
or model-development decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

SUPPORTED_CLASS_NAME = (
    "supported_tomato_leaf"
)

UNSUPPORTED_CLASS_NAME = (
    "unsupported_image"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the binary KILIMO subject-validation dataset."
        )
    )

    parser.add_argument(
        "--tomato-root",
        type=Path,
        required=True,
        help=(
            "Root directory containing the existing tomato disease "
            "image folders."
        ),
    )

    parser.add_argument(
        "--unsupported-root",
        type=Path,
        required=True,
        help=(
            "Root directory containing unsupported images. "
            "Subdirectories are allowed and are scanned recursively."
        ),
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(
            "subject_dataset"
        ),
        help=(
            "Destination directory for train/val/test dataset."
        ),
    )

    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.70,
    )

    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--max-supported",
        type=int,
        default=5000,
        help=(
            "Maximum number of supported images to use."
        ),
    )

    parser.add_argument(
        "--max-unsupported",
        type=int,
        default=5000,
        help=(
            "Maximum number of unsupported images to use."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Delete the existing output directory before creation."
        ),
    )

    return parser.parse_args()


def discover_images(
    root: Path,
) -> list[Path]:
    """
    Recursively discover supported image files.
    """

    if not root.exists():
        raise FileNotFoundError(
            f"Directory does not exist: {root}"
        )

    images = []

    for path in root.rglob("*"):

        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        ):
            images.append(
                path
            )

    return sorted(
        images
    )


def is_decodable_image(
    path: Path,
) -> bool:
    """
    Verify that Pillow can decode the image.
    """

    try:

        with Image.open(
            path
        ) as image:

            image.verify()

        return True

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):

        return False


def remove_corrupt_images(
    paths: list[Path],
) -> tuple[
    list[Path],
    list[Path],
]:
    """
    Separate decodable and invalid images.
    """

    valid = []
    invalid = []

    for path in paths:

        if is_decodable_image(
            path
        ):
            valid.append(
                path
            )

        else:
            invalid.append(
                path
            )

    return valid, invalid


def file_signature(
    path: Path,
) -> str:
    """
    Calculate a SHA-256 digest for duplicate detection.
    """

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file_handle:

        while True:

            chunk = file_handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def remove_exact_duplicates(
    paths: list[Path],
) -> tuple[
    list[Path],
    int,
]:
    """
    Remove byte-identical duplicate image files.
    """

    seen = set()

    unique = []

    duplicates = 0

    for path in paths:

        signature = file_signature(
            path
        )

        if signature in seen:

            duplicates += 1

            continue

        seen.add(
            signature
        )

        unique.append(
            path
        )

    return unique, duplicates


def sample_paths(
    paths: list[Path],
    maximum: int,
    random_generator: random.Random,
) -> list[Path]:
    """
    Deterministically limit the number of examples.
    """

    paths = list(
        paths
    )

    random_generator.shuffle(
        paths
    )

    if maximum > 0:

        paths = paths[
            :maximum
        ]

    return paths


def calculate_split_sizes(
    total: int,
    train_ratio: float,
    val_ratio: float,
) -> tuple[
    int,
    int,
    int,
]:
    """
    Calculate exact split counts.
    """

    train_count = int(
        total
        * train_ratio
    )

    val_count = int(
        total
        * val_ratio
    )

    test_count = (
        total
        - train_count
        - val_count
    )

    return (
        train_count,
        val_count,
        test_count,
    )


def split_paths(
    paths: list[Path],
    train_ratio: float,
    val_ratio: float,
    random_generator: random.Random,
) -> dict[
    str,
    list[Path],
]:
    """
    Deterministically split one class.
    """

    paths = list(
        paths
    )

    random_generator.shuffle(
        paths
    )

    train_count, val_count, _ = (
        calculate_split_sizes(
            len(paths),
            train_ratio,
            val_ratio,
        )
    )

    train_end = train_count

    val_end = (
        train_count
        + val_count
    )

    return {
        "train":
            paths[
                :train_end
            ],

        "val":
            paths[
                train_end:
                val_end
            ],

        "test":
            paths[
                val_end:
            ],
    }


def copy_split(
    split_name: str,
    class_name: str,
    paths: list[Path],
    output_root: Path,
) -> None:
    """
    Copy one dataset split into ImageFolder layout.
    """

    destination = (
        output_root
        / split_name
        / class_name
    )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    for index, source in enumerate(
        paths
    ):

        suffix = source.suffix.lower()

        destination_name = (
            f"{class_name}_{index:06d}"
            f"{suffix}"
        )

        shutil.copy2(
            source,
            destination
            / destination_name,
        )


def main() -> None:

    args = parse_args()

    ratio_sum = (
        args.train_ratio
        + args.val_ratio
        + args.test_ratio
    )

    if abs(
        ratio_sum
        - 1.0
    ) > 1e-6:

        raise ValueError(
            "Train, validation and test ratios "
            "must sum to 1.0."
        )

    random_generator = (
        random.Random(
            args.seed
        )
    )

    if (
        args.output_root.exists()
        and args.overwrite
    ):

        shutil.rmtree(
            args.output_root
        )

    if args.output_root.exists():

        raise FileExistsError(
            f"Output directory already exists: "
            f"{args.output_root}. "
            "Use --overwrite to replace it."
        )

    print(
        "Discovering supported tomato images..."
    )

    supported_paths = discover_images(
        args.tomato_root
    )

    print(
        f"Found {len(supported_paths)} "
        "candidate supported images."
    )

    print(
        "Discovering unsupported images..."
    )

    unsupported_paths = discover_images(
        args.unsupported_root
    )

    print(
        f"Found {len(unsupported_paths)} "
        "candidate unsupported images."
    )

    supported_paths, supported_invalid = (
        remove_corrupt_images(
            supported_paths
        )
    )

    unsupported_paths, unsupported_invalid = (
        remove_corrupt_images(
            unsupported_paths
        )
    )

    supported_paths, supported_duplicates = (
        remove_exact_duplicates(
            supported_paths
        )
    )

    unsupported_paths, unsupported_duplicates = (
        remove_exact_duplicates(
            unsupported_paths
        )
    )

    supported_paths = sample_paths(
        supported_paths,
        args.max_supported,
        random_generator,
    )

    unsupported_paths = sample_paths(
        unsupported_paths,
        args.max_unsupported,
        random_generator,
    )

    if len(
        supported_paths
    ) < 100:

        raise RuntimeError(
            "Too few supported tomato-leaf images "
            "were found."
        )

    if len(
        unsupported_paths
    ) < 100:

        raise RuntimeError(
            "Too few unsupported images were found."
        )

    supported_splits = split_paths(
        supported_paths,
        args.train_ratio,
        args.val_ratio,
        random_generator,
    )

    unsupported_splits = split_paths(
        unsupported_paths,
        args.train_ratio,
        args.val_ratio,
        random_generator,
    )

    for split_name in (
        "train",
        "val",
        "test",
    ):

        copy_split(
            split_name,
            SUPPORTED_CLASS_NAME,
            supported_splits[
                split_name
            ],
            args.output_root,
        )

        copy_split(
            split_name,
            UNSUPPORTED_CLASS_NAME,
            unsupported_splits[
                split_name
            ],
            args.output_root,
        )

    metadata = {
        "seed":
            args.seed,

        "ratios": {
            "train":
                args.train_ratio,

            "val":
                args.val_ratio,

            "test":
                args.test_ratio,
        },

        "class_names": [
            UNSUPPORTED_CLASS_NAME,
            SUPPORTED_CLASS_NAME,
        ],

        "counts": {
            "supported": {
                split:
                    len(
                        supported_splits[
                            split
                        ]
                    )
                for split in (
                    "train",
                    "val",
                    "test",
                )
            },

            "unsupported": {
                split:
                    len(
                        unsupported_splits[
                            split
                        ]
                    )
                for split in (
                    "train",
                    "val",
                    "test",
                )
            },
        },

        "discarded": {
            "supported_corrupt":
                len(
                    supported_invalid
                ),

            "unsupported_corrupt":
                len(
                    unsupported_invalid
                ),

            "supported_exact_duplicates":
                supported_duplicates,

            "unsupported_exact_duplicates":
                unsupported_duplicates,
        },
    }

    metadata_path = (
        args.output_root
        / "dataset_metadata.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Subject dataset created successfully."
    )

    print(
        f"Output: "
        f"{args.output_root.resolve()}"
    )

    print()
    print(
        json.dumps(
            metadata,
            indent=2,
        )
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Do not use the test split to choose "
        "training settings or thresholds."
    )


if __name__ == "__main__":
    main()