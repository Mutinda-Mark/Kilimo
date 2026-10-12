"""
CNN model definition and checkpoint utilities.

Architecture: EfficientNet-B0 pretrained on ImageNet, with its final
classifier layer replaced by a Linear(1280 → NUM_CLASSES) head.

Why EfficientNet-B0?
  - ~5.3 M parameters — small enough for fast CPU inference on a VM.
  - Achieves >93% top-1 on ImageNet despite the compact size.
  - The final feature map is 1280-dimensional, giving the Grad-CAM
    layer (Phase 2) a rich representation to work with.
  - The target convolutional layer for Grad-CAM is `model.features[-1]`.

Training strategy (implemented in train_colab.py):
  Phase A — warm-up (backbone frozen)
      Only the classifier head trains; learning rate = 1e-3.
      This prevents the pretrained weights from being destroyed by the
      large initial gradients from a randomly initialised head.
  Phase B — full fine-tune (all layers unfrozen)
      All layers train; learning rate = 1e-4.
      A lower LR protects the pretrained feature extractors while still
      allowing the whole network to adapt to tomato leaf images.
"""

import torch
import torch.nn as nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

from cv.config import DISEASE_CLASSES, NUM_CLASSES


# ── Model construction ────────────────────────────────────────────────────────

def build_model(num_classes: int = NUM_CLASSES, pretrained: bool = True) -> nn.Module:
    """
    Build and return the EfficientNet-B0 model with a custom head.

    Args:
        num_classes: Number of output classes (default: NUM_CLASSES = 7).
        pretrained:  Load ImageNet weights. Set False when loading from a
                     local checkpoint (the weights will be loaded separately).

    Returns:
        torch.nn.Module ready for training or inference.
    """
    weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
    model = efficientnet_b0(weights=weights)

    # The original classifier is:  Dropout(0.2) → Linear(1280 → 1000)
    # We keep the Dropout and replace only the Linear layer.
    in_features: int = model.classifier[1].in_features  # 1280
    model.classifier[1] = nn.Linear(in_features, num_classes)

    return model


# ── Gradient flow helpers ─────────────────────────────────────────────────────

def freeze_backbone(model: nn.Module) -> None:
    """
    Freeze every parameter except the classifier head.

    Call this before Phase A (warm-up) training so only the new head
    receives gradient updates.
    """
    for name, param in model.named_parameters():
        param.requires_grad = "classifier" in name


def unfreeze_all(model: nn.Module) -> None:
    """
    Unfreeze all parameters.

    Call this before Phase B (full fine-tune) training.
    """
    for param in model.parameters():
        param.requires_grad = True


def count_trainable_params(model: nn.Module) -> int:
    """Return the number of parameters that will receive gradient updates."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# ── Checkpoint utilities ──────────────────────────────────────────────────────

def save_checkpoint(
    model: nn.Module,
    path: str,
    val_acc: float,
    epoch: int,
) -> None:
    """
    Save a model checkpoint.

    The checkpoint stores the state dict alongside metadata (class names,
    backbone identifier) so the correct architecture can be reconstructed
    by load_checkpoint() without extra arguments.

    Args:
        model:   The nn.Module to save.
        path:    Destination file path (e.g. "cv/weights/best_model.pt").
        val_acc: Validation accuracy at the time of saving (stored as metadata).
        epoch:   Epoch number at the time of saving.
    """
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "val_acc": val_acc,
            "epoch": epoch,
            "num_classes": NUM_CLASSES,
            "disease_classes": DISEASE_CLASSES,
            "backbone": "efficientnet_b0",
        },
        path,
    )


def load_checkpoint(path: str, device: str = "cpu") -> nn.Module:
    """
    Load a model from a checkpoint saved by save_checkpoint().

    Args:
        path:   Path to the .pt checkpoint file.
        device: Target device ("cpu" or "cuda").

    Returns:
        nn.Module in eval() mode, ready for inference.

    Raises:
        FileNotFoundError: If `path` does not exist.
        RuntimeError: If the checkpoint is missing required keys.
    """
    checkpoint: dict = torch.load(path, map_location=device, weights_only=False)

    required_keys = {"model_state_dict", "num_classes", "disease_classes"}
    missing = required_keys - checkpoint.keys()
    if missing:
        raise RuntimeError(
            f"Checkpoint at '{path}' is missing required keys: {missing}. "
            "Make sure it was saved by save_checkpoint() from this project."
        )

    model = build_model(num_classes=checkpoint["num_classes"], pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model
