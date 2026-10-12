# ============================================================
# Phase 1 — CNN Tomato Disease Classifier
# Google Colab Training Script
# ============================================================
#
# HOW TO USE:
# -----------------------------------------------------------
# 1. Open https://colab.research.google.com
# 2. Runtime > Change runtime type > GPU (T4 or better)
# 3. Upload this file:  File > Upload to session storage
# 4. Run each cell in order (each section below is one cell)
# 5. At the end, download  best_model.pt  and place it at:
#       tomato_advisory_backend/cv/weights/best_model.pt
#
# Cell markers (# %%) are recognised by VS Code's Jupyter
# extension so you can also run this locally with a GPU.
# -----------------------------------------------------------
#
# Expected training time on a Colab T4 GPU:
#   Phase A (frozen backbone, 5 epochs):  ~8 minutes
#   Phase B (full fine-tune, 20 epochs):  ~40 minutes
# -----------------------------------------------------------

# %% [markdown]
# ## Cell 1 — Install dependencies

# %%
# Colab ships with torch pre-installed. We only need grad-cam here;
# the rest are already available on Colab's standard image.
# !pip install grad-cam --quiet

# %% [markdown]
# ## Cell 2 — Imports and reproducibility seed

# %%
import json
import os
import random
import shutil
import warnings
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

warnings.filterwarnings("ignore")

# ── Reproducibility ────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# ── Device ──────────────────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")
if DEVICE.type == "cuda":
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# %% [markdown]
# ## Cell 3 — Configuration
#
# Everything in one place. Changing NUM_CLASSES or DISEASE_CLASSES here
# must be mirrored in cv/config.py before running local inference.

# %%
# ── Disease classes (order defines the integer label) ───────
DISEASE_CLASSES = [
    "Early Blight",        # 0
    "Late Blight",         # 1
    "Bacterial Spot",      # 2
    "Leaf Mold",           # 3
    "Septoria Leaf Spot",  # 4
    "Tomato Mosaic Virus", # 5
    "Healthy",             # 6
]
NUM_CLASSES = len(DISEASE_CLASSES)

# Maps Kaggle folder names → canonical class name above.
# Folders NOT in this dict are ignored (drops unwanted classes).
FOLDER_TO_CLASS = {
    "Tomato___Early_blight":           "Early Blight",
    "Tomato___Late_blight":            "Late Blight",
    "Tomato___Bacterial_spot":         "Bacterial Spot",
    "Tomato___Leaf_Mold":              "Leaf Mold",
    "Tomato___Septoria_leaf_spot":     "Septoria Leaf Spot",
    "Tomato___Tomato_mosaic_virus":    "Tomato Mosaic Virus",
    "Tomato___healthy":                "Healthy",
    # Single-underscore variants
    "Tomato_Early_blight":             "Early Blight",
    "Tomato_Late_blight":              "Late Blight",
    "Tomato_Bacterial_spot":           "Bacterial Spot",
    "Tomato_Leaf_Mold":                "Leaf Mold",
    "Tomato_Septoria_leaf_spot":       "Septoria Leaf Spot",
    "Tomato_mosaic_virus":             "Tomato Mosaic Virus",
    "Tomato_healthy":                  "Healthy",
}

# ── Training hyperparameters ────────────────────────────────
IMAGE_SIZE      = 224
BATCH_SIZE      = 32
NUM_WORKERS     = 2        # reduce to 0 if DataLoader hangs on Colab
# Phase A: frozen backbone warm-up
PHASE_A_EPOCHS  = 5
PHASE_A_LR      = 1e-3
# Phase B: full fine-tune
PHASE_B_EPOCHS  = 25
PHASE_B_LR      = 1e-4
PHASE_B_PATIENCE = 7       # early-stopping patience

# ── Paths ────────────────────────────────────────────────────
DATA_ROOT    = Path("tomato-disease-multiple-sources")  # extracted dataset root
SAVE_DIR     = Path("outputs")
SAVE_DIR.mkdir(exist_ok=True)
CHECKPOINT   = SAVE_DIR / "best_model.pt"

print(f"Classes ({NUM_CLASSES}):", DISEASE_CLASSES)

# %% [markdown]
# ## Cell 4 — Download dataset from Kaggle
#
# **Option A (recommended):** Use the Kaggle API.
#   1. Go to https://www.kaggle.com/settings → API → Create New Token
#   2. Upload the downloaded `kaggle.json` when the cell prompts you.
#
# **Option B (manual):** Download the zip from Kaggle in your browser,
#   upload it to Colab (File > Upload), then skip to the unzip step.

# %%
import os

USE_KAGGLE_API = True  # set False if you uploaded the zip manually

if USE_KAGGLE_API:
    from google.colab import files
    print("Upload your kaggle.json API token:")
    uploaded = files.upload()

    os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)
    shutil.copy("kaggle.json", os.path.expanduser("~/.kaggle/kaggle.json"))
    os.chmod(os.path.expanduser("~/.kaggle/kaggle.json"), 0o600)

    os.system(
        "kaggle datasets download -d cookiefinder/tomato-disease-multiple-sources --quiet"
    )
    ZIP_FILE = "tomato-disease-multiple-sources.zip"
else:
    # Change this to the name of the zip you uploaded manually
    ZIP_FILE = "tomato-disease-multiple-sources.zip"

print(f"Extracting {ZIP_FILE} ...")
with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(".")
print("Done.")

# %% [markdown]
# ## Cell 5 — Explore and validate dataset structure

# %%
def find_split_dirs(root: Path) -> tuple[Path, Path]:
    """
    Locate train/ and val/ (or test/) directories under `root`.

    The Kaggle dataset may have the splits at the top level or nested
    one level deeper — this handles both layouts automatically.
    """
    for candidate in [root, *root.iterdir()]:
        if not candidate.is_dir():
            continue
        children = {d.name.lower() for d in candidate.iterdir() if d.is_dir()}
        if "train" in children and ("val" in children or "valid" in children or "test" in children):
            train_dir = candidate / "train"
            val_dir = candidate / ("val" if (candidate / "val").exists() else
                                   "valid" if (candidate / "valid").exists() else "test")
            return train_dir, val_dir
    raise FileNotFoundError(
        f"Could not find train/ and val/ directories under '{root}'. "
        "Check the zip extraction output above."
    )


train_dir, val_dir = find_split_dirs(DATA_ROOT)
print(f"Train dir : {train_dir}")
print(f"Val dir   : {val_dir}")
print()

# Show which folders will be used vs skipped
print("Dataset folder analysis:")
class_counts: dict[str, dict[str, int]] = {}

for split, split_dir in [("train", train_dir), ("val", val_dir)]:
    for folder in sorted(split_dir.iterdir()):
        if not folder.is_dir():
            continue
        n_images = len(list(folder.glob("*.jpg")) + list(folder.glob("*.png")) +
                       list(folder.glob("*.JPG")) + list(folder.glob("*.PNG")))
        mapped_class = FOLDER_TO_CLASS.get(folder.name, "⛔ SKIPPED")
        status = "✓" if mapped_class != "⛔ SKIPPED" else "✗"
        print(f"  {status} [{split}] {folder.name:<50} → {mapped_class} ({n_images} images)")

        if mapped_class != "⛔ SKIPPED":
            if mapped_class not in class_counts:
                class_counts[mapped_class] = {"train": 0, "val": 0}
            class_counts[mapped_class][split] += n_images

print()
print("Class summary:")
for cls, counts in class_counts.items():
    print(f"  {cls:<30} train: {counts['train']:>5}  val: {counts['val']:>5}")

# %% [markdown]
# ## Cell 6 — Dataset class and transforms

# %%
class TomatoDataset(Dataset):
    """
    Custom dataset that:
      - Loads images from a directory tree (one subfolder per class)
      - Applies the FOLDER_TO_CLASS mapping to filter unwanted classes
      - Accepts a torchvision transform pipeline

    Args:
        root_dir:  Path to train/ or val/ directory.
        transform: torchvision transform to apply to each image.
    """

    def __init__(self, root_dir: Path, transform=None) -> None:
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples: list[tuple[Path, int]] = []

        # Build label map: canonical class name → integer index
        self.class_to_idx = {cls: idx for idx, cls in enumerate(DISEASE_CLASSES)}

        for folder in sorted(self.root_dir.iterdir()):
            if not folder.is_dir():
                continue
            class_name = FOLDER_TO_CLASS.get(folder.name)
            if class_name is None:
                continue  # skip unwanted classes

            label = self.class_to_idx[class_name]
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"):
                for img_path in folder.glob(ext):
                    self.samples.append((img_path, label))

        if not self.samples:
            raise ValueError(
                f"No samples found in '{root_dir}'. "
                "Check that FOLDER_TO_CLASS keys match the actual folder names."
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as exc:
            raise RuntimeError(f"Failed to load image '{img_path}': {exc}") from exc

        if self.transform:
            image = self.transform(image)
        return image, label


class RandomJPEGCompression:
    """
    Custom transform that simulates WhatsApp's JPEG recompression.

    WhatsApp compresses images to roughly 70-85% JPEG quality before
    forwarding them. Training with this augmentation makes the model
    more robust to the quality loss it will see in production.
    """

    def __init__(self, quality_range: tuple[int, int] = (60, 90)) -> None:
        self.quality_range = quality_range

    def __call__(self, img: Image.Image) -> Image.Image:
        import io
        quality = random.randint(*self.quality_range)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return Image.open(buffer).copy()  # .copy() detaches from the buffer


# ── Transforms ────────────────────────────────────────────────────────────────
# ImageNet mean/std because EfficientNet-B0 was pretrained on ImageNet.

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(p=0.1),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
    transforms.RandomRotation(15),
    RandomJPEGCompression(quality_range=(65, 90)),   # WhatsApp simulation
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

val_transform = transforms.Compose([
    # IMPORTANT: these must exactly match TomatoPredictor._INFERENCE_TRANSFORM
    # in cv/predictor.py so training and production preprocessing are identical.
    transforms.Resize(256),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

# %% [markdown]
# ## Cell 7 — Build data loaders with class-imbalance correction

# %%
train_dataset = TomatoDataset(train_dir, transform=train_transform)
val_dataset   = TomatoDataset(val_dir,   transform=val_transform)

print(f"Training samples   : {len(train_dataset):,}")
print(f"Validation samples : {len(val_dataset):,}")

# ── Weighted sampler to correct class imbalance ───────────────────────────────
# Instead of oversampling minority classes by duplicating images, we use a
# WeightedRandomSampler so each class gets roughly equal representation in
# every batch, without modifying the underlying dataset.

train_labels   = [label for _, label in train_dataset.samples]
class_counts_  = np.bincount(train_labels, minlength=NUM_CLASSES)
class_weights  = 1.0 / np.where(class_counts_ > 0, class_counts_, 1)
sample_weights = [class_weights[label] for label in train_labels]

sampler = WeightedRandomSampler(
    weights=sample_weights,
    num_samples=len(train_dataset),
    replacement=True,
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    sampler=sampler,       # shuffle=False when using a sampler
    num_workers=NUM_WORKERS,
    pin_memory=DEVICE.type == "cuda",
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=DEVICE.type == "cuda",
)

# Report class distribution
print("\nClass distribution in training set:")
for i, cls in enumerate(DISEASE_CLASSES):
    print(f"  {cls:<30} {class_counts_[i]:>5} images  (weight: {class_weights[i]:.6f})")

# ── Loss function ────────────────────────────────────────────────────────────
# Even though the sampler balances batches, we also pass class weights to the
# loss function as a belt-and-suspenders measure.
loss_weights = torch.tensor(class_weights / class_weights.sum(), dtype=torch.float32).to(DEVICE)
criterion = nn.CrossEntropyLoss(weight=loss_weights)

# %% [markdown]
# ## Cell 8 — Build model

# %%
def build_model(num_classes: int = NUM_CLASSES, pretrained: bool = True) -> nn.Module:
    weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
    model   = efficientnet_b0(weights=weights)
    in_features = model.classifier[1].in_features  # 1280
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

def freeze_backbone(model: nn.Module) -> None:
    for name, param in model.named_parameters():
        param.requires_grad = "classifier" in name

def unfreeze_all(model: nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = True

model = build_model(pretrained=True).to(DEVICE)

# Confirm the target layer for Grad-CAM (Phase 2)
gradcam_target_layer = model.features[-1]
print("Grad-CAM target layer:", gradcam_target_layer.__class__.__name__)

total_params = sum(p.numel() for p in model.parameters())
print(f"Total parameters: {total_params:,}")

# %% [markdown]
# ## Cell 9 — Training utilities

# %%
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    scaler,          # GradScaler or None (no mixed precision on CPU)
) -> tuple[float, float]:
    """Train for one epoch. Returns (avg_loss, accuracy_%)."""
    model.train()
    total_loss = 0.0
    correct    = 0
    total      = 0
    n_batches  = len(loader)

    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()

        if scaler is not None:                            # GPU: mixed precision
            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss    = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:                                             # CPU: standard precision
            outputs = model(images)
            loss    = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        total_loss += loss.item()
        preds       = outputs.argmax(dim=1)
        correct    += preds.eq(labels).sum().item()
        total      += labels.size(0)

        if (batch_idx + 1) % 20 == 0 or batch_idx == n_batches - 1:
            print(
                f"  Batch {batch_idx + 1}/{n_batches} | "
                f"Loss: {loss.item():.4f} | "
                f"Acc: {100. * correct / total:.2f}%",
                end="\r",
            )

    print()  # newline after the \r progress line
    return total_loss / n_batches, 100.0 * correct / total


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
) -> tuple[float, float]:
    """Evaluate without gradient tracking. Returns (avg_loss, accuracy_%)."""
    model.eval()
    total_loss = 0.0
    correct    = 0
    total      = 0

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        outputs         = model(images)
        loss            = criterion(outputs, labels)
        total_loss     += loss.item()
        preds           = outputs.argmax(dim=1)
        correct        += preds.eq(labels).sum().item()
        total          += labels.size(0)

    return total_loss / len(loader), 100.0 * correct / total


def run_training_phase(
    model: nn.Module,
    phase_name: str,
    num_epochs: int,
    lr: float,
    patience: int = 999,          # no early stopping by default in Phase A
    best_val_acc: float = 0.0,
) -> tuple[dict, float]:
    """
    Run one training phase (A or B).

    Returns:
        history:      dict of loss/acc lists
        best_val_acc: best validation accuracy achieved
    """
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr,
        weight_decay=1e-4,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=lr * 0.01)
    scaler    = torch.cuda.amp.GradScaler() if DEVICE.type == "cuda" else None

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    patience_counter = 0

    for epoch in range(1, num_epochs + 1):
        print(f"\n[{phase_name}] Epoch {epoch}/{num_epochs}  (LR: {scheduler.get_last_lr()[0]:.2e})")

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, scaler)
        val_loss,   val_acc   = evaluate(model, val_loader, criterion)
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        print(
            f"  Train → Loss: {train_loss:.4f}  Acc: {train_acc:.2f}%\n"
            f"  Val   → Loss: {val_loss:.4f}  Acc: {val_acc:.2f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc     = val_acc
            patience_counter = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "val_acc":          best_val_acc,
                    "epoch":            epoch,
                    "phase":            phase_name,
                    "num_classes":      NUM_CLASSES,
                    "disease_classes":  DISEASE_CLASSES,
                    "backbone":         "efficientnet_b0",
                },
                CHECKPOINT,
            )
            print(f"  ✅ New best! Saved checkpoint (val_acc = {best_val_acc:.2f}%)")
        else:
            patience_counter += 1
            print(f"  No improvement ({patience_counter}/{patience})")
            if patience_counter >= patience:
                print(f"  ⏹  Early stopping triggered at epoch {epoch}.")
                break

    return history, best_val_acc

# %% [markdown]
# ## Cell 10 — Phase A: warm-up (frozen backbone)
#
# The backbone's pretrained ImageNet weights are frozen.
# Only the 7-class head trains. This avoids the random head's large
# initial gradients from corrupting the pretrained feature extractor.

# %%
print("=" * 60)
print("PHASE A — Warm-up (frozen backbone)")
print("=" * 60)

freeze_backbone(model)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Trainable parameters: {trainable:,}  (head only)")

history_a, best_acc_a = run_training_phase(
    model,
    phase_name="Phase A",
    num_epochs=PHASE_A_EPOCHS,
    lr=PHASE_A_LR,
    patience=999,           # no early stopping in warm-up
    best_val_acc=0.0,
)

print(f"\nPhase A complete. Best val acc: {best_acc_a:.2f}%")

# %% [markdown]
# ## Cell 11 — Phase B: full fine-tune (all layers unfrozen)

# %%
print("=" * 60)
print("PHASE B — Full fine-tune (all layers unfrozen)")
print("=" * 60)

# Load the best Phase A checkpoint before continuing
checkpoint = torch.load(CHECKPOINT, map_location=DEVICE)
model.load_state_dict(checkpoint["model_state_dict"])

unfreeze_all(model)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Trainable parameters: {trainable:,}  (all layers)")

history_b, best_acc_b = run_training_phase(
    model,
    phase_name="Phase B",
    num_epochs=PHASE_B_EPOCHS,
    lr=PHASE_B_LR,
    patience=PHASE_B_PATIENCE,
    best_val_acc=best_acc_a,   # keep Phase A best as the bar to beat
)

print(f"\nPhase B complete. Overall best val acc: {best_acc_b:.2f}%")
print(f"PRD target: >90.00% → {'✅ PASSED' if best_acc_b > 90.0 else '❌ NOT YET MET'}")

# %% [markdown]
# ## Cell 12 — Evaluation: confusion matrix & classification report

# %%
# Reload the best checkpoint for evaluation
checkpoint = torch.load(CHECKPOINT, map_location=DEVICE)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

all_preds  = []
all_labels = []

with torch.no_grad():
    for images, labels in val_loader:
        images = images.to(DEVICE)
        outputs = model(images)
        preds   = outputs.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds.tolist())
        all_labels.extend(labels.numpy().tolist())

all_preds  = np.array(all_preds)
all_labels = np.array(all_labels)

# ── Confusion matrix ──────────────────────────────────────────
cm = confusion_matrix(all_labels, all_preds)
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
plt.colorbar(im)
tick_marks = np.arange(NUM_CLASSES)
ax.set_xticks(tick_marks)
ax.set_yticks(tick_marks)
ax.set_xticklabels(DISEASE_CLASSES, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(DISEASE_CLASSES, fontsize=9)

thresh = cm.max() / 2.0
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black", fontsize=8)

ax.set_ylabel("True label")
ax.set_xlabel("Predicted label")
ax.set_title(f"Confusion Matrix — Val Acc: {best_acc_b:.2f}%")
plt.tight_layout()
plt.savefig(SAVE_DIR / "confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: outputs/confusion_matrix.png")

# ── Classification report ─────────────────────────────────────
report = classification_report(all_labels, all_preds, target_names=DISEASE_CLASSES, digits=4)
print("\nClassification Report:")
print(report)
with open(SAVE_DIR / "classification_report.txt", "w") as f:
    f.write(report)
print("Saved: outputs/classification_report.txt")

# ── Training history plot ─────────────────────────────────────
combined_acc  = history_a["val_acc"]  + history_b["val_acc"]
combined_loss = history_a["val_loss"] + history_b["val_loss"]
phase_boundary = len(history_a["val_acc"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
ax1.plot(combined_acc)
ax1.axvline(x=phase_boundary - 0.5, color="gray", linestyle="--", label="Phase A→B")
ax1.axhline(y=90, color="red", linestyle=":", label="Target (90%)")
ax1.set_title("Validation Accuracy")
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Accuracy (%)")
ax1.legend()

ax2.plot(combined_loss)
ax2.axvline(x=phase_boundary - 0.5, color="gray", linestyle="--", label="Phase A→B")
ax2.set_title("Validation Loss")
ax2.set_xlabel("Epoch")
ax2.set_ylabel("Loss")
ax2.legend()

plt.tight_layout()
plt.savefig(SAVE_DIR / "training_history.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: outputs/training_history.png")

# ── Save training history JSON ────────────────────────────────
full_history = {
    "phase_a": history_a,
    "phase_b": history_b,
    "best_val_acc": best_acc_b,
    "phase_boundary_epoch": phase_boundary,
}
with open(SAVE_DIR / "training_history.json", "w") as f:
    json.dump(full_history, f, indent=2)
print("Saved: outputs/training_history.json")

# %% [markdown]
# ## Cell 13 — Download model weights
#
# Downloads `best_model.pt` to your local machine.
# Place it at:  tomato_advisory_backend/cv/weights/best_model.pt

# %%
print(f"Checkpoint path : {CHECKPOINT}")
print(f"File size       : {CHECKPOINT.stat().st_size / 1e6:.1f} MB")
print(f"Best val acc    : {best_acc_b:.2f}%")

# Option A: Download directly from Colab
from google.colab import files  # noqa: E402
files.download(str(CHECKPOINT))

# Option B: Save to Google Drive (uncomment if you want a Drive backup)
# from google.colab import drive
# drive.mount("/content/drive")
# shutil.copy(CHECKPOINT, "/content/drive/MyDrive/tomato_advisory/best_model.pt")
# print("Also saved to Google Drive.")

print("\n✅ Phase 1 complete!")
print("Next: copy best_model.pt → tomato_advisory_backend/cv/weights/best_model.pt")
print("Then run:  pytest tests/test_predictor.py  to verify local inference.")
