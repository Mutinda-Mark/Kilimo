# Sprint III Requirements Traceability

This document records the implementation, testing, evaluation, evidence,
and completion status of the remaining Sprint III requirements for KILIMO.

A requirement is marked as completed only after the implemented behaviour
has been tested and supporting evidence has been recorded.

---

## 1. Image Quality and Input Validation

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| IQ-01 | Reject technically unusable blurred or featureless images before disease inference | `cv/image_quality.py` image-quality gate | `tests/test_image_quality.py` | Synthetic featureless image rejected with reason `blur` | Pytest output: 7 image-quality unit tests passed | Completed - algorithmic test |
| IQ-02 | Reject excessively dark images | `cv/image_quality.py` brightness validation | `test_rejects_dark_image` | Dark image rejected with reason `too_dark` | Pytest output | Completed |
| IQ-03 | Reject excessively bright images | `cv/image_quality.py` brightness validation | `test_rejects_overexposed_image` | Bright image rejected with reason `too_bright` | Pytest output | Completed |
| IQ-04 | Reject images below the configured minimum resolution | `cv/image_quality.py` dimension validation | `test_rejects_small_image` | Small image rejected with reason `low_resolution` | Pytest output | Completed |
| IQ-05 | Reject unsupported image formats and oversized inputs | MIME/file-size validation | `test_rejects_unsupported_mime_type`, `test_rejects_oversized_file` | Invalid inputs rejected safely | Pytest output | Completed |
| IQ-06 | Provide actionable correction guidance for rejected images | `ImageAnalysisService` rejection response | `test_rejected_image_returns_actionable_message` | Blurry image returns retake/focus guidance | Pytest output | Completed |
| IQ-07 | Prevent rejected images from reaching disease inference | `ImageAnalysisService` returns before `TomatoAssessor.assess()` | `test_rejected_image_does_not_call_assessor` | Assessor, advisory engine and responder were not called | Pytest output | Completed |
| IQ-08 | Preserve existing backend behaviour after introducing the quality gate | Existing backend regression suite | Full `pytest -q --tb=short` | 92 tests passed, 0 failed | Full pytest output | Completed |
| IQ-09 | Validate blur and lighting thresholds using representative real phone photographs | Pending real-world evaluation | Real clear, blurred, dark and overexposed tomato images | Not yet evaluated | Pending | In Progress |

---

## 2. Tomato Subject Validation

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| SV-01 | Prevent clearly unsupported subjects from reaching the tomato disease classifier | `cv/subject_validator.py` | Application-contract tests | Supported/unsupported states behave correctly using controlled model outputs | `tests/test_subject_validator.py` - 5 passed | In Progress |
| SV-02 | Return an explicit unsupported-subject state instead of forcing a disease class | `TomatoSubjectValidator` | `test_subject_validator_rejects_unsupported_score` | Unsupported result returned correctly | Pytest output | In Progress |
| SV-03 | Abstain when subject suitability is uncertain | Three-state subject-validation policy | `test_subject_validator_abstains_on_uncertain_score` | Uncertain score returns abstention state | Pytest output | In Progress |
| SV-04 | Train a tomato-leaf vs unsupported-image model | Planned MobileNetV3-Small binary classifier | Training and validation | Not yet trained | Pending | Pending |
| SV-05 | Evaluate the subject validator on held-out supported and unsupported images | Pending model evaluation | Precision, recall, F1, confusion matrix, false-acceptance and false-rejection analysis | Not yet evaluated | Pending | Pending |
| SV-06 | Integrate the trained subject validator before EfficientNet disease inference | Pending service integration | End-to-end tests | Not yet implemented | Pending | Pending |

---

## 3. Multiple Image Assessment

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| MI-01 | Allow a farmer to submit multiple images for one assessment | Planned WhatsApp batch workflow | Pending | Pending | Pending | Pending |
| MI-02 | Validate each image independently before inference | Planned quality + subject-validation pipeline | Pending | Pending | Pending | Pending |
| MI-03 | Aggregate model evidence from accepted images | Planned batch assessment service | Pending | Pending | Pending | Pending |
| MI-04 | Detect inconsistent predictions across images | Planned agreement/abstention policy | Pending | Pending | Pending | Pending |
| MI-05 | Reject unusable images without discarding valid images from the same batch | Planned partial-success workflow | Pending | Pending | Pending | Pending |
| MI-06 | Limit the number and size of submitted images | Planned maximum of 3 images and server-side limits | Pending | Pending | Pending | Pending |

---

## 4. Administrative Completion

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| AD-01 | Administrator can view their own profile | Planned profile page | Pending | Pending | Pending | Pending |
| AD-02 | Administrator settings are available and persist meaningful preferences | Planned settings page | Pending | Pending | Pending | Pending |
| AD-03 | Dashboard exposes useful image-validation statistics where appropriate | Planned analytics extension | Pending | Pending | Pending | Pending |

---

## 5. AI Uncertainty and Result Presentation

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| AI-UNC-01 | Review use of the term `confidence` for raw classifier scores | Pending terminology review | Report/interface review | Pending | Pending | In Progress |
| AI-UNC-02 | Define an evaluated abstention policy | Subject validator and multi-image workflow | Pending evaluation | Pending | Pending | Pending |
| AI-UNC-03 | Present uncertainty without implying diagnostic certainty | Planned farmer-facing result updates | Pending usability/evaluation | Pending | Pending | Pending |

---

## 6. Deployment and Operational Release

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| DEP-01 | Deploy a working HTTPS backend | Pending | Live smoke test | Pending | Pending | Pending |
| DEP-02 | Connect deployed backend to real PostgreSQL database | Pending | Database health test | Pending | Pending | Pending |
| DEP-03 | Serve the evaluated model in the deployed environment | Pending | Live prediction test | Pending | Pending | Pending |
| DEP-04 | Deploy and connect the administrative dashboard | Pending | End-to-end admin test | Pending | Pending | Pending |
| DEP-05 | Verify WhatsApp against the deployed backend | Pending | Live WhatsApp test | Pending | Pending | Pending |

---

## 7. Reproducibility and Handover

| ID | Requirement | Implementation | Test / Evaluation | Actual Result | Evidence | Status |
|---|---|---|---|---|---|---|
| DOC-01 | README supports setup on a clean beginner machine | README overhaul planned | Independent setup dry run | Pending | Pending | Pending |
| DOC-02 | Document database setup and troubleshooting | Pending README update | Clean-machine setup | Pending | Pending | Pending |
| DOC-03 | Document model acquisition/training | Pending README update | Reproduction check | Pending | Pending | Pending |
| DOC-04 | Document Meta WhatsApp configuration | Pending README update | Reproduction check | Pending | Pending | Pending |
| DOC-05 | Document Supabase OAuth and TOTP setup | Pending README update | Reproduction check | Pending | Pending | Pending |