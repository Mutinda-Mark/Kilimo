# KILIMO — Sprint I and Sprint II Development Evidence

This document records the implementation activities, technical evidence, testing results, corrective actions, and system functionality completed during the first two development sprints of the KILIMO Tomato Disease Detection and Farmer Advisory System.

---

# Sprint I — Project Setup, Environment and Model Development

## Sprint Objective

Sprint I focused on establishing the technical foundation required for the KILIMO system.

The sprint covered:

- Backend environment configuration
- Frontend environment configuration
- PostgreSQL database setup
- Computer vision dataset preparation
- EfficientNet-B0 training pipeline development
- Project source-code organization
- External API configuration
- Git and GitHub setup
- Secret protection
- Testing environment preparation
- Reproducible project setup

---

## Sprint I Tasks and Evidence

| ID | Task | Status | Evidence |
|---|---|---|---|
| S1-01 | Configure Python backend development environment | Completed | Python virtual environment, FastAPI application and `requirements.txt` |
| S1-02 | Configure frontend development environment | Completed | Next.js, TypeScript, Tailwind CSS and `package.json` |
| S1-03 | Configure PostgreSQL database | Completed | Sessions, conversation history, assessments and WhatsApp event tables |
| S1-04 | Prepare tomato disease dataset and training pipeline | Completed | Training notebook and EfficientNet-B0 training pipeline |
| S1-05 | Organize project source code | Completed | Separate backend, computer vision, NLP, service, WhatsApp, admin and test modules |
| S1-06 | Configure external APIs | Completed | Gemini API and Meta WhatsApp Cloud API integration |
| S1-07 | Set up Git version control | Completed | Git repository initialized and pushed to GitHub |
| S1-08 | Protect secrets from version control | Completed | `.gitignore` and example environment files |
| S1-09 | Add reproducible setup instructions | Completed | Root README and dependency files |
| S1-10 | Prepare automated testing environment | Completed | pytest, pytest-asyncio, ESLint and Next.js production build |

---

## Development Environment

### Backend

The backend development environment uses:

- Python
- FastAPI
- PostgreSQL
- PyTorch
- torchvision
- Pillow
- asyncpg
- Google Gemini API
- Meta WhatsApp Cloud API

### Frontend

The administrative dashboard uses:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts

### Development Tools

The project development environment includes:

- Visual Studio Code
- Git
- GitHub
- Google Colab
- PowerShell
- pytest
- ESLint

---

## Code Organization

The KILIMO codebase is organized into two major application areas:

```text
Kilimo/
├── backend/
│   ├── app/
│   │   ├── admin/
│   │   ├── services/
│   │   └── whatsapp/
│   ├── cv/
│   ├── nlp/
│   └── tests/
│
├── admin-dashboard/
│   └── src/
│
├── docs/
├── .gitignore
└── README.md
```

The modular structure separates:

- Computer vision processing
- Natural language processing
- Database services
- WhatsApp communication
- Administrative functionality
- Automated testing

This structure improves separation of concerns and makes individual system components easier to maintain and test.

---

## Data Preparation

The computer vision component was developed using labelled tomato leaf disease images.

The implemented model supports the following **11 classes**:

1. Bacterial Spot
2. Early Blight
3. Late Blight
4. Leaf Mold
5. Septoria Leaf Spot
6. Spider Mites / Two-Spotted Spider Mite
7. Target Spot
8. Tomato Yellow Leaf Curl Virus
9. Tomato Mosaic Virus
10. Healthy
11. Powdery Mildew

Image preprocessing and augmentation were incorporated into the training pipeline.

The trained model weights are stored separately from the Git repository because binary model checkpoints are excluded from normal version control.

---

## Model Development Evidence

The image classification model uses **EfficientNet-B0** as the classification backbone together with transfer learning.

Training was completed in two major phases:

- Phase A — Initial Training
- Phase B — Fine-Tuning

---

### Phase A — Initial Training

Five initial training epochs were performed.

Training accuracy increased from approximately:

```text
66.76% → 75.95%
```

Validation accuracy increased from approximately:

```text
77.48% → 81.07%
```

Validation loss decreased from approximately:

```text
0.6920 → 0.5668
```

These results indicated that the model was learning meaningful visual features from the tomato disease dataset during the initial training phase.

---

### Phase B — Fine-Tuning

The model was subsequently fine-tuned for an additional **16 epochs**.

Training accuracy increased from approximately:

```text
86.87% → 99.44%
```

Validation accuracy increased from approximately:

```text
93.84% → 98.79%
```

The highest validation accuracy recorded during development was:

```text
98.79%
```

> **Important:** The 98.79% value represents validation performance during model development and is not treated as final held-out test accuracy.

---

## Version Control Evidence

Git version control was formally introduced after the initial local prototype had already been implemented.

### Initial Repository Commit

```text
12fd4a1 Initial project baseline: integrated KILIMO prototype
```

### GitHub Repository

```text
https://github.com/Mutinda-Mark/Kilimo
```

The repository excludes sensitive and unnecessary generated files, including:

- API keys
- Database passwords
- WhatsApp credentials
- Gemini credentials
- `.env` files
- Python virtual environments
- `node_modules`
- Next.js build output
- Trained model weights

This helps reduce the risk of accidentally exposing confidential application credentials or unnecessarily storing large generated files in the repository.

---

## Sprint I Outcome

Sprint I established a working and reproducible development environment for the KILIMO system.

By the end of the sprint:

- The FastAPI backend had been configured.
- The Next.js administrative frontend had been configured.
- PostgreSQL persistence had been established.
- The computer vision training pipeline had been implemented.
- EfficientNet-B0 training and fine-tuning had been completed.
- External services had been configured.
- Git and GitHub version control had been established.
- Automated testing tools had been prepared.
- Secrets and large generated files had been excluded from version control.

The completion of Sprint I provided the technical foundation required for implementation of the integrated farmer advisory workflow.

---

# Sprint II — Core Functionality, Integration and Initial Testing

## Sprint Objective

Sprint II focused on implementing and integrating the primary KILIMO workflow.

The main objective was to allow a farmer to provide input through WhatsApp and receive either:

- A tomato disease assessment from an uploaded leaf image, or
- An agricultural advisory response from a text question.

The sprint also introduced contextual conversation handling, data persistence, duplicate-message protection, the administrative dashboard, and initial automated testing.

---

## Core System Workflow

The integrated KILIMO workflow is:

```text
Farmer
   |
   v
WhatsApp
   |
   v
Meta WhatsApp Cloud API
   |
   v
FastAPI Webhook
   |
   v
Message Validation and Duplicate Check
   |
   +-----------------------------+
   |                             |
   v                             v
Text Input                    Image Input
   |                             |
   v                             v
NLP / RAG                  EfficientNet-B0
   |                             |
   |                        Disease Prediction
   |                             |
   |                        Grad-CAM Analysis
   |                             |
   |                        Severity Estimate
   |                             |
   +-------------+---------------+
                 |
                 v
         Advisory Generation
                 |
                 v
             PostgreSQL
                 |
                 v
         WhatsApp Response
```

This workflow integrates the main KILIMO components into a single farmer-facing interaction process.

---

## Sprint II Core Functionality

| ID | Feature | Status |
|---|---|---|
| S2-01 | Receive WhatsApp text messages | Completed |
| S2-02 | Receive WhatsApp tomato leaf images | Completed |
| S2-03 | Classify tomato leaf disease | Completed |
| S2-04 | Generate confidence score | Completed |
| S2-05 | Generate Grad-CAM activation | Completed |
| S2-06 | Estimate disease severity | Completed |
| S2-07 | Generate structured disease advisory | Completed |
| S2-08 | Retrieve agricultural information using RAG | Completed |
| S2-09 | Generate natural-language responses using Gemini | Completed |
| S2-10 | Maintain farmer conversation context | Completed |
| S2-11 | Store assessment history | Completed |
| S2-12 | Prevent duplicate WhatsApp processing | Completed |
| S2-13 | Provide administrative monitoring dashboard | Completed |
| S2-14 | Provide assessment and analytics views | Completed |

---

## Implemented Database Resources

The PostgreSQL database currently stores information required for farmer sessions, conversations, assessments, WhatsApp processing, and agricultural knowledge retrieval.

### `sessions`

The `sessions` resource maintains farmer session context using the farmer's WhatsApp phone number.

It allows the system to associate new farmer messages with an existing conversation.

---

### `conversation_history`

The `conversation_history` resource stores conversational interactions between the farmer and KILIMO.

This enables the system to retain recent conversational context for follow-up questions.

---

### `assessments`

The `assessments` resource stores historical tomato image assessment results.

Stored information includes:

- Disease
- Prediction confidence
- Severity
- Affected area percentage
- Assessment source
- Timestamps

This allows previous disease assessments to be retrieved and displayed within the administrative dashboard.

---

### `whatsapp_messages`

The `whatsapp_messages` resource stores incoming Meta WhatsApp message IDs and their processing state.

This is used to prevent duplicate processing when Meta sends the same webhook event more than once.

---

### Disease and RAG Data

The database also stores agricultural information and semantic retrieval resources used by the natural language advisory pipeline.

These resources support:

- Disease information retrieval
- Contextual advisory generation
- Semantic search
- RAG processing
- Farmer follow-up questions

---

# Initial Testing Evidence

## Automated Backend Testing

The backend uses:

- `pytest`
- `pytest-asyncio`

Automated tests currently cover:

- API health
- Image validation
- Prediction
- Disease assessment
- Severity estimation
- Grad-CAM processing
- Advisory generation
- Embeddings
- RAG retrieval
- Responder behavior
- Farmer sessions
- Conversation flow
- Validation failures
- Failure handling
- WhatsApp webhook processing
- Duplicate WhatsApp messages

---

## Initial Test Record

| Test ID | Test | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| TC-01 | Backend health endpoint | API responds successfully | API responded successfully | Pass |
| TC-02 | Valid tomato image | Disease prediction returned | Prediction returned | Pass |
| TC-03 | Empty farmer phone number | Request rejected | Validation error returned | Pass |
| TC-04 | Empty text question | Request rejected | Validation error returned | Pass |
| TC-05 | New farmer text query | Session created automatically | Session created | Pass |
| TC-06 | Follow-up query | Previous assessment context retained | Context retained | Pass |
| TC-07 | Image assessment | Assessment stored in PostgreSQL | Assessment stored | Pass |
| TC-08 | Healthy image result | Severity set to `None` and affected area to `0%` | Normalized successfully | Pass |
| TC-09 | Duplicate WhatsApp message | Message ignored after first processing | Duplicate rejected | Pass |
| TC-10 | Failed internal image processing | Safe public error returned | Generic error returned | Pass |
| TC-11 | RAG retrieval | Relevant disease context included | Relevant context retrieved | Pass |
| TC-12 | Farmer follow-up question | Query includes disease and question context | Context included | Pass |
| TC-13 | Admin dashboard lint | No lint errors | Passed | Pass |
| TC-14 | Admin production build | Production build completes | Passed | Pass |

---

# Corrective Actions During Development

Several defects and inconsistencies were identified during initial testing.

The issues were investigated and corrected during Sprint II.

---

## 1. Service Dependency Mocking

### Problem

Some automated tests patched module-level objects after the application services had already captured references to those dependencies.

### Effect

Real computer vision and Gemini components were unintentionally executed during automated tests.

This reduced test isolation and could make test behavior dependent on external resources.

### Correction

The tests were changed so that dependencies are patched directly on the instantiated service objects.

### Result

Chat and image-flow tests became deterministic and better isolated from production dependencies.

---

## 2. Healthy Severity Handling

### Problem

The disease severity estimation pipeline could generate an affected-area result even when the image classifier predicted that the tomato leaf was healthy.

This could create contradictory output, such as a healthy prediction accompanied by a non-zero affected-area percentage.

### Correction

Healthy predictions are normalized before database persistence and advisory generation.

### Current Behavior

```text
Disease: Healthy
Severity: None
Affected area: 0%
```

### Result

Healthy assessments now produce consistent classification and severity information.

---

## 3. WhatsApp Duplicate Processing

### Problem

Meta may deliver the same webhook message more than once.

Without protection, the same farmer message could therefore be processed repeatedly and result in duplicate responses.

### Correction

Incoming WhatsApp message IDs are claimed in the PostgreSQL database before background processing begins.

### Result

Previously completed messages are not processed a second time.

This provides duplicate-message protection for webhook events.

---

## 4. Webhook Response Time

### Problem

Computer vision and AI processing can require more time than a simple webhook acknowledgment.

Performing long-running processing directly inside the webhook request could delay the acknowledgment returned to Meta.

### Correction

Long-running processing was moved to FastAPI `BackgroundTasks`.

### Result

The webhook can acknowledge incoming requests quickly while the application performs computer vision, NLP, database, and response-generation operations separately.

---

## 5. RAG Test Expectations

### Problem

Earlier automated tests expected outdated prompt headings and retrieval queries based only on the farmer's current question.

The implementation later evolved to include additional contextual information.

### Correction

The tests were updated to reflect the current contextual RAG query structure.

### Result

RAG tests now verify the behavior of the current system rather than obsolete implementation details.

---

# Administrative Dashboard

The KILIMO administrative dashboard provides monitoring and analytical capabilities for the implemented system.

Available dashboard functionality includes:

- System overview
- Farmer sessions
- Farmer conversation history
- Assessment history
- Assessment details
- Disease distribution
- Severity distribution
- Data source statistics
- Activity analytics
- WhatsApp processing information
- Database information
- Model information

---

## Frontend Validation

The frontend was validated using:

```bash
npm run lint
```

and:

```bash
npm run build
```

Both checks completed successfully during development.

The linting process verifies code-quality requirements, while the production build verifies that the Next.js application can compile successfully for production use.

---

# Sprint II Outcome

Sprint II successfully integrated the main KILIMO system components into a working farmer advisory workflow.

By the end of the sprint, the system could:

- Receive farmer messages through WhatsApp
- Receive tomato leaf images
- Validate incoming messages
- Prevent duplicate processing
- Classify tomato diseases
- Generate prediction confidence
- Produce Grad-CAM analysis
- Estimate disease severity
- Generate structured advisory information
- Retrieve agricultural information using RAG
- Generate contextual natural-language responses
- Maintain farmer conversation history
- Persist disease assessments
- Store WhatsApp processing records
- Provide administrative monitoring
- Display assessment and analytical information
- Execute automated backend tests
- Pass frontend lint and production build validation

Sprint II therefore established the first integrated and testable version of the complete KILIMO farmer interaction workflow.

---

# Overall Development Progress

The first two sprints established both the technical foundation and the main functional workflow of KILIMO.

## Sprint I Delivered

- Development environment
- Project structure
- Database setup
- Model training pipeline
- EfficientNet-B0 model development
- Git and GitHub repository
- External API configuration
- Testing environment

## Sprint II Delivered

- WhatsApp communication
- Image disease assessment
- Confidence scoring
- Grad-CAM analysis
- Severity estimation
- RAG-based retrieval
- Contextual advisory generation
- Farmer session management
- Assessment persistence
- Duplicate-message protection
- Administrative dashboard
- Automated testing
- Initial defect correction

Together, these two sprints provide the foundation for subsequent work involving system hardening, final model evaluation, end-to-end acceptance testing, usability evaluation, deployment, and final academic documentation.