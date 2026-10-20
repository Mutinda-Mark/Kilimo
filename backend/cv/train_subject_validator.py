"""
Train the KILIMO tomato subject-validation model.

Model:
    MobileNetV3-Small

Task:
    Binary classification

Classes:
    unsupported_image
    supported_tomato_leaf

The script:
    - trains using the train split
    - selects the best checkpoint using validation loss
    - records training history
    - evaluates validation behaviour
    - DOES NOT use the held-out test split for training decisions

The final test split should be evaluated separately after the
model and threshold policy are frozen.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from PIL import ImageFile
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


ImageFile.LOAD_TRUNCATED_IMAGES = False


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


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "subject_validator_output"
        ),
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--weight-decay",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=4,
    )

    return parser.parse_args()


def set_seed(
    seed: int,
) -> None:

    random.seed(
        seed
    )

    np.random.seed(
        seed
    )

    torch.manual_seed(
        seed
    )

    if torch.cuda.is_available():

        torch.cuda.manual_seed_all(
            seed
        )


def build_transforms():

    train_transform = transforms.Compose(
        [
            transforms.Resize(
                256
            ),

            transforms.RandomResizedCrop(
                224,
                scale=(
                    0.80,
                    1.0,
                ),
            ),

            transforms.RandomHorizontalFlip(),

            transforms.RandomRotation(
                degrees=12
            ),

            transforms.ColorJitter(
                brightness=0.15,
                contrast=0.15,
                saturation=0.10,
            ),

            transforms.ToTensor(),

            transforms.Normalize(
                mean=IMAGENET_MEAN,
                std=IMAGENET_STD,
            ),
        ]
    )

    eval_transform = transforms.Compose(
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

    return (
        train_transform,
        eval_transform,
    )


def build_datasets(
    dataset_root: Path,
):

    train_transform, eval_transform = (
        build_transforms()
    )

    train_dataset = (
        datasets.ImageFolder(
            dataset_root
            / "train",
            transform=train_transform,
        )
    )

    val_dataset = (
        datasets.ImageFolder(
            dataset_root
            / "val",
            transform=eval_transform,
        )
    )

    expected_classes = [
        "supported_tomato_leaf",
        "unsupported_image",
    ]

    if set(
        train_dataset.classes
    ) != set(
        expected_classes
    ):

        raise RuntimeError(
            "Unexpected dataset classes. "
            f"Found: {train_dataset.classes}"
        )

    if (
        train_dataset.class_to_idx
        != val_dataset.class_to_idx
    ):

        raise RuntimeError(
            "Train and validation class mappings differ."
        )

    return (
        train_dataset,
        val_dataset,
    )


def build_model() -> nn.Module:

    weights = (
        models.MobileNet_V3_Small_Weights.DEFAULT
    )

    model = (
        models.mobilenet_v3_small(
            weights=weights
        )
    )

    in_features = (
        model.classifier[-1].in_features
    )

    model.classifier[-1] = (
        nn.Linear(
            in_features,
            1,
        )
    )

    return model


def calculate_pos_weight(
    dataset: datasets.ImageFolder,
) -> torch.Tensor:
    """
    Calculate BCE positive-class weighting.

    Positive class:
        supported_tomato_leaf
    """

    class_to_idx = (
        dataset.class_to_idx
    )

    positive_index = (
        class_to_idx[
            "supported_tomato_leaf"
        ]
    )

    positive_count = sum(
        1
        for _, label in dataset.samples
        if label == positive_index
    )

    negative_count = (
        len(
            dataset.samples
        )
        - positive_count
    )

    if (
        positive_count == 0
        or negative_count == 0
    ):

        raise RuntimeError(
            "Both binary classes must contain images."
        )

    value = (
        negative_count
        / positive_count
    )

    return torch.tensor(
        [
            value
        ],
        dtype=torch.float32,
    )


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[
    float,
    float,
]:

    model.train()

    total_loss = 0.0

    probabilities = []

    targets = []

    for images, labels in loader:

        images = images.to(
            device
        )

        labels = labels.to(
            device
        )

        # ImageFolder alphabetically maps:
        #
        # supported_tomato_leaf -> usually 0
        # unsupported_image    -> usually 1
        #
        # But our binary model defines:
        #
        # tomato leaf  -> 1
        # unsupported  -> 0
        #
        # Therefore derive the binary target
        # explicitly from the class mapping outside
        # alphabetic assumptions.

        supported_index = (
            loader.dataset.class_to_idx[
                "supported_tomato_leaf"
            ]
        )

        binary_targets = (
            labels
            == supported_index
        ).float()

        optimizer.zero_grad(
            set_to_none=True
        )

        logits = model(
            images
        ).squeeze(
            1
        )

        loss = criterion(
            logits,
            binary_targets,
        )

        loss.backward()

        optimizer.step()

        total_loss += (
            loss.item()
            * images.size(
                0
            )
        )

        probs = torch.sigmoid(
            logits
        )

        probabilities.extend(
            probs.detach()
            .cpu()
            .tolist()
        )

        targets.extend(
            binary_targets.detach()
            .cpu()
            .int()
            .tolist()
        )

    average_loss = (
        total_loss
        / len(
            loader.dataset
        )
    )

    predicted = [
        1
        if probability >= 0.5
        else 0
        for probability
        in probabilities
    ]

    accuracy = accuracy_score(
        targets,
        predicted,
    )

    return (
        average_loss,
        float(
            accuracy
        ),
    )


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> dict:

    model.eval()

    total_loss = 0.0

    probabilities = []

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

        labels = labels.to(
            device
        )

        binary_targets = (
            labels
            == supported_index
        ).float()

        logits = model(
            images
        ).squeeze(
            1
        )

        loss = criterion(
            logits,
            binary_targets,
        )

        total_loss += (
            loss.item()
            * images.size(
                0
            )
        )

        probs = torch.sigmoid(
            logits
        )

        probabilities.extend(
            probs.cpu()
            .tolist()
        )

        targets.extend(
            binary_targets.cpu()
            .int()
            .tolist()
        )

    predicted = [
        1
        if probability >= 0.5
        else 0
        for probability
        in probabilities
    ]

    accuracy = accuracy_score(
        targets,
        predicted,
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            targets,
            predicted,
            average="binary",
            zero_division=0,
        )
    )

    confusion = confusion_matrix(
        targets,
        predicted,
        labels=[
            0,
            1,
        ],
    )

    try:

        roc_auc = roc_auc_score(
            targets,
            probabilities,
        )

    except ValueError:

        roc_auc = None

    return {
        "loss":
            total_loss
            / len(
                loader.dataset
            ),

        "accuracy":
            float(
                accuracy
            ),

        "precision":
            float(
                precision
            ),

        "recall":
            float(
                recall
            ),

        "f1":
            float(
                f1
            ),

        "roc_auc":
            (
                float(
                    roc_auc
                )
                if roc_auc is not None
                else None
            ),

        "confusion_matrix":
            confusion.tolist(),

        "targets":
            targets,

        "probabilities":
            probabilities,
    }


def save_checkpoint(
    model: nn.Module,
    output_path: Path,
    class_to_idx: dict,
    epoch: int,
    validation_metrics: dict,
) -> None:

    checkpoint = {
        "model_state_dict":
            model.state_dict(),

        "architecture":
            "mobilenet_v3_small",

        "task":
            "tomato_subject_validation",

        "positive_class":
            "supported_tomato_leaf",

        "class_to_idx":
            class_to_idx,

        "epoch":
            epoch,

        "validation_metrics": {
            key:
                value
            for key, value
            in validation_metrics.items()
            if key not in {
                "targets",
                "probabilities",
            }
        },
    }

    torch.save(
        checkpoint,
        output_path,
    )


def main() -> None:

    args = parse_args()

    set_seed(
        args.seed
    )

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"Device: {device}"
    )

    train_dataset, val_dataset = (
        build_datasets(
            args.dataset_root
        )
    )

    print(
        "Class mapping:",
        train_dataset.class_to_idx,
    )

    print(
        f"Train samples: "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation samples: "
        f"{len(val_dataset)}"
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    model = build_model().to(
        device
    )

    pos_weight = calculate_pos_weight(
        train_dataset
    ).to(
        device
    )

    criterion = (
        nn.BCEWithLogitsLoss(
            pos_weight=pos_weight
        )
    )

    optimizer = AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    best_val_loss = float(
        "inf"
    )

    epochs_without_improvement = 0

    history = []

    best_checkpoint_path = (
        args.output_dir
        / "tomato_subject_validator.pt"
    )

    print()

    for epoch in range(
        1,
        args.epochs
        + 1,
    ):

        start_time = time.time()

        train_loss, train_accuracy = (
            train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
            )
        )

        validation = evaluate(
            model,
            val_loader,
            criterion,
            device,
        )

        elapsed = (
            time.time()
            - start_time
        )

        epoch_record = {
            "epoch":
                epoch,

            "train_loss":
                train_loss,

            "train_accuracy":
                train_accuracy,

            "val_loss":
                validation[
                    "loss"
                ],

            "val_accuracy":
                validation[
                    "accuracy"
                ],

            "val_precision":
                validation[
                    "precision"
                ],

            "val_recall":
                validation[
                    "recall"
                ],

            "val_f1":
                validation[
                    "f1"
                ],

            "val_roc_auc":
                validation[
                    "roc_auc"
                ],

            "seconds":
                elapsed,
        }

        history.append(
            epoch_record
        )

        print(
            f"Epoch {epoch:02d} | "
            f"train loss {train_loss:.4f} | "
            f"train acc {train_accuracy:.4f} | "
            f"val loss {validation['loss']:.4f} | "
            f"val acc {validation['accuracy']:.4f} | "
            f"val F1 {validation['f1']:.4f}"
        )

        if (
            validation[
                "loss"
            ]
            < best_val_loss
        ):

            best_val_loss = (
                validation[
                    "loss"
                ]
            )

            epochs_without_improvement = 0

            save_checkpoint(
                model,
                best_checkpoint_path,
                train_dataset.class_to_idx,
                epoch,
                validation,
            )

            print(
                "  -> saved new best checkpoint"
            )

        else:

            epochs_without_improvement += 1

            if (
                epochs_without_improvement
                >= args.patience
            ):

                print(
                    "Early stopping triggered."
                )

                break

    history_path = (
        args.output_dir
        / "training_history.json"
    )

    history_path.write_text(
        json.dumps(
            history,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Training complete."
    )

    print(
        "Best checkpoint:"
    )

    print(
        best_checkpoint_path.resolve()
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Do not evaluate the held-out test split "
        "until model and threshold decisions are frozen."
    )


if __name__ == "__main__":
    main()