"""
Analyse tomato-subject validation thresholds.

This script uses ONLY the validation split.

It does not evaluate the held-out test set.

The purpose is to inspect the trade-off between:

    false acceptance:
        unsupported image accepted as tomato

    false rejection:
        tomato leaf rejected as unsupported

    abstention:
        image falls between unsupported and supported thresholds
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


IMAGENET_MEAN = [
    0.485,
    0.456,
    0.406,
]

IMAGENET_STD = [
    0.229,
    0.224,
    0.225,
]


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "subject_threshold_analysis.json"
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
    )

    return parser.parse_args()


def build_model():

    model = models.mobilenet_v3_small(
        weights=None
    )

    in_features = (
        model.classifier[-1].in_features
    )

    model.classifier[-1] = (
        torch.nn.Linear(
            in_features,
            1,
        )
    )

    return model


@torch.no_grad()
def collect_scores(
    model,
    loader,
    device,
):

    model.eval()

    scores = []

    targets = []

    supported_index = (
        loader.dataset.class_to_idx[
            "supported_tomato_leaf"
        ]
    )

    for images, labels in loader:

        images = images.to(
            device
        )

        logits = model(
            images
        ).squeeze(
            1
        )

        probabilities = torch.sigmoid(
            logits
        )

        binary_targets = (
            labels
            == supported_index
        ).int()

        scores.extend(
            probabilities.cpu()
            .tolist()
        )

        targets.extend(
            binary_targets.tolist()
        )

    return (
        np.asarray(
            scores,
            dtype=np.float64,
        ),
        np.asarray(
            targets,
            dtype=np.int64,
        ),
    )


def evaluate_pair(
    scores,
    targets,
    unsupported_threshold,
    supported_threshold,
):

    supported_mask = (
        scores
        >= supported_threshold
    )

    unsupported_mask = (
        scores
        <= unsupported_threshold
    )

    uncertain_mask = ~(
        supported_mask
        | unsupported_mask
    )

    actual_supported = (
        targets == 1
    )

    actual_unsupported = (
        targets == 0
    )

    false_acceptances = np.sum(
        supported_mask
        & actual_unsupported
    )

    false_rejections = np.sum(
        unsupported_mask
        & actual_supported
    )

    unsupported_total = np.sum(
        actual_unsupported
    )

    supported_total = np.sum(
        actual_supported
    )

    total = len(
        targets
    )

    return {
        "unsupported_threshold":
            round(
                float(
                    unsupported_threshold
                ),
                2,
            ),

        "supported_threshold":
            round(
                float(
                    supported_threshold
                ),
                2,
            ),

        "false_acceptance_rate":
            (
                float(
                    false_acceptances
                    / unsupported_total
                )
                if unsupported_total
                else 0.0
            ),

        "false_rejection_rate":
            (
                float(
                    false_rejections
                    / supported_total
                )
                if supported_total
                else 0.0
            ),

        "abstention_rate":
            float(
                np.sum(
                    uncertain_mask
                )
                / total
            ),

        "accepted_supported":
            int(
                np.sum(
                    supported_mask
                    & actual_supported
                )
            ),

        "incorrectly_accepted_unsupported":
            int(
                false_acceptances
            ),

        "incorrectly_rejected_supported":
            int(
                false_rejections
            ),

        "uncertain_count":
            int(
                np.sum(
                    uncertain_mask
                )
            ),
    }


def main():

    args = parse_args()

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    transform = transforms.Compose(
        [
            transforms.Resize(
                256
            ),

            transforms.CenterCrop(
                224
            ),

            transforms.ToTensor(),

            transforms.Normalize(
                mean=IMAGENET_MEAN,
                std=IMAGENET_STD,
            ),
        ]
    )

    dataset = datasets.ImageFolder(
        args.dataset_root
        / "val",
        transform=transform,
    )

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
    )

    checkpoint = torch.load(
        args.checkpoint,
        map_location=device,
    )

    model = build_model()

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    model.to(
        device
    )

    scores, targets = collect_scores(
        model,
        loader,
        device,
    )

    candidate_pairs = [
        (
            0.20,
            0.80,
        ),
        (
            0.25,
            0.75,
        ),
        (
            0.30,
            0.70,
        ),
        (
            0.35,
            0.65,
        ),
        (
            0.40,
            0.60,
        ),
    ]

    results = [
        evaluate_pair(
            scores,
            targets,
            unsupported_threshold,
            supported_threshold,
        )
        for (
            unsupported_threshold,
            supported_threshold,
        )
        in candidate_pairs
    ]

    output = {
        "note": (
            "Validation split only. "
            "Held-out test split not evaluated."
        ),

        "total_validation_images":
            int(
                len(
                    targets
                )
            ),

        "candidates":
            results,
    }

    args.output.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            output,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()