# KILIMO — Tomato Disease Detection and Farmer Advisory System

KILIMO is a smartphone-based tomato disease detection and farmer advisory system developed using **computer vision**, **natural language processing**, and **cloud-based messaging technologies**.

The system enables tomato farmers to interact through **WhatsApp** by submitting tomato leaf images and text-based questions. Submitted images pass through technical quality checks and tomato-subject validation before disease assessment.

KILIMO supports both **single-image and multi-image assessments**. A farmer may submit up to three usable tomato leaf images for one assessment, and the system aggregates the resulting predictions before generating a final disease assessment.

The advisory component uses a **Retrieval-Augmented Generation (RAG)** pipeline together with **Google Gemini** to generate farmer-friendly responses grounded in agricultural knowledge and recent conversation context.

A secure administrative dashboard provides access to farmer sessions, assessments, analytics, system status and operational information.

---

# Project Overview

KILIMO was developed as a final-year **BSc Informatics and Computer Science** project at **Strathmore University**.

The final system combines:

- WhatsApp-based farmer interaction
- Technical image-quality validation
- Tomato-subject validation
- Multi-image tomato assessment
- EfficientNet-B0 disease classification
- Grad-CAM-based model interpretation
- Disease severity estimation
- Retrieval-Augmented Generation
- Context-aware farmer interaction
- Google Gemini response generation
- PostgreSQL persistence
- FastAPI backend services
- Next.js administrative dashboard
- Supabase database and administrator authentication
- Google OAuth and TOTP MFA
- Microsoft Azure App Service deployment
- Vercel dashboard deployment
- GitHub Actions CI/CD
- Git LFS model artefact management

---

# Final System Architecture

The deployed system follows the general workflow below:

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
Azure FastAPI Webhook
  |
  v
Webhook Verification
  |
  v
Message Deduplication
  |
  v
WhatsApp Processor
  |
  +------------------------------+
  |                              |
  v                              v
Image Processing             Text Processing
  |                              |
  v                              v
Image Quality Gate            Session Context
  |                              |
  v                              v
Tomato Subject Validator      RAG Retrieval
  |                              |
  v                              v
Multi-Image Batch             Gemini
  |
  v
EfficientNet-B0
  |
  v
Grad-CAM + Severity
  |
  v
Multi-Image Aggregation
  |
  +--------------+---------------+
                 |
                 v
          Farmer Advisory
                 |
                 v
          PostgreSQL / Supabase
                 |
                 v
             WhatsApp
```

Administrative monitoring follows a separate protected path:

```text
Administrator
     |
     v
Google OAuth
     |
     v
TOTP MFA
     |
     v
Vercel Next.js Dashboard
     |
     v
Protected FastAPI Admin API
     |
     v
PostgreSQL / Supabase
```

---

# Supported Tomato Classes

The final disease-classification model supports **11 classes**:

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

---

# Computer Vision Models

KILIMO uses multiple computer-vision components.

## Disease Classifier

The primary disease-classification model is:

```text
EfficientNet-B0
```

The model was trained using transfer learning and fine-tuned on labelled tomato disease images.

Recorded held-out performance:

```text
Accuracy: approximately 98.79%
Macro F1-score: approximately 98.90%
```

EfficientNet-B0 was selected over MobileNetV3-Large because it achieved slightly stronger classification performance while remaining sufficiently efficient for the intended application.

## Comparison Model

A **MobileNetV3-Large** model was also trained for comparison.

Recorded held-out performance:

```text
Accuracy: approximately 98.71%
Macro F1-score: approximately 98.84%
```

MobileNetV3-Large achieved faster model-level inference, while EfficientNet-B0 achieved slightly stronger classification performance.

## Tomato Subject Validator

A separate **MobileNetV3-Small** binary classifier is used before disease classification.

Its role is to determine whether a submitted image represents a supported tomato-leaf subject.

The validator supports three practical outcomes:

```text
SUPPORTED
UNCERTAIN
UNSUPPORTED
```

The thresholds were selected conservatively because the main operational priority was to reduce unsupported images being accepted as valid tomato inputs.

---

# Image Quality Validation

Before an image reaches the machine-learning pipeline, KILIMO performs technical image-quality validation.

Checks include:

- Supported file format
- Minimum image dimensions
- File-size restrictions
- Brightness
- Blur
- Image decoding validity

Poor-quality images are rejected before disease inference.

Rejected images do not consume one of the farmer's available assessment image slots.

---

# Multi-Image Assessment

KILIMO supports up to **three usable tomato leaf images per assessment**.

The farmer may:

```text
Send 1 image → reply DONE
Send 2 images → reply DONE
Send 3 images → assessment automatically starts
```

The `DONE` command allows the farmer to finalise an assessment early.

## Aggregation Behaviour

For one accepted image:

```text
The individual image result is used.
```

For two accepted images:

```text
The predictions must sufficiently agree.
```

For three accepted images:

```text
At least two predictions must agree.
```

Where sufficient agreement does not exist, KILIMO abstains from presenting a potentially misleading combined diagnosis.

Only one combined assessment is stored for the final image batch.

---

# Disease Severity Estimation

Grad-CAM is used to identify image regions contributing strongly to the predicted disease class.

Image-processing heuristics then estimate the visible affected area and map the result to an advisory severity level.

For images predicted as:

```text
Healthy
```

KILIMO normalises the result to:

```text
Severity: None
Affected area: 0.0%
```

Severity estimates should be interpreted as advisory image-based estimates rather than laboratory-confirmed disease measurements.

---

# Natural Language Advisory and RAG

The advisory pipeline combines:

- Structured disease information
- Farmer question
- Previous assessment context
- Recent conversation history
- Semantic retrieval
- Agricultural knowledge chunks
- Google Gemini response generation

A farmer can therefore ask follow-up questions such as:

```text
How can I stop it from spreading?

How serious is it?

What should I do next?

How can I prevent this next season?
```

The farmer does not need to repeat the disease name after every message because session context is maintained in PostgreSQL.

---

# Farmer Conversation Example

A typical multi-image interaction may look like:

```text
Farmer:
[Uploads tomato leaf image]

KILIMO:
Photo 1 received and accepted.
You can send up to 2 more usable photos
or reply DONE to analyse the photos now.

Farmer:
[Uploads another image]

KILIMO:
Photo 2 received and accepted.
You can send 1 more usable photo
or reply DONE to analyse the photos now.

Farmer:
DONE

KILIMO:
Multi-image assessment (2/2 photos agreed):

The images are most consistent with Early Blight.

Severity: Moderate

Recommended actions:
- Remove badly affected leaves
- Reduce prolonged leaf moisture
- Monitor neighbouring tomato plants
- Follow appropriate disease-management guidance

Farmer:
How do I stop it spreading?

KILIMO:
Provides a contextual response based on the
previous assessment and retrieved agricultural knowledge.
```

---

# Project Structure

```text
Kilimo/
|
├── backend/
│   ├── app/
│   │   ├── admin/
│   │   ├── security/
│   │   ├── services/
│   │   ├── whatsapp/
│   │   ├── config.py
│   │   ├── db.py
│   │   └── main.py
│   │
│   ├── cv/
│   │   ├── weights/
│   │   ├── assessor.py
│   │   ├── config.py
│   │   ├── gradcam.py
│   │   ├── image_quality.py
│   │   ├── model.py
│   │   ├── predictor.py
│   │   ├── subject_validator.py
│   │   ├── train_subject_validator.py
│   │   └── prepare_subject_dataset.py
│   │
│   ├── nlp/
│   │   ├── advisory.py
│   │   ├── embeddings.py
│   │   ├── knowledge.py
│   │   ├── rag.py
│   │   ├── responder.py
│   │   └── seed_knowledge.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   ├── .python-version
│   └── .env.example
│
├── admin-dashboard/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── lib/
│   ├── public/
│   ├── package.json
│   └── .env.local.example
│
├── docs/
├── .github/
│   └── workflows/
├── .gitattributes
├── .gitignore
└── README.md
```

---

# Main Technologies

## Backend

- Python 3.13
- FastAPI
- PostgreSQL
- asyncpg
- PyTorch
- torchvision
- Pillow
- OpenCV Headless
- Google Gemini API
- Meta WhatsApp Cloud API

## Computer Vision

- EfficientNet-B0
- MobileNetV3-Large
- MobileNetV3-Small
- Grad-CAM
- Image-quality validation
- Multi-image aggregation

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts

## Authentication and Database

- Supabase PostgreSQL
- Supabase Auth
- Google OAuth
- TOTP MFA

## Deployment

- Microsoft Azure App Service
- Vercel
- GitHub Actions
- Git LFS

## Testing and Development

- pytest
- pytest-asyncio
- ESLint
- Git
- GitHub
- Google Colab
- Visual Studio Code

---

# Backend Setup

## 1. Clone the Repository

```bash
git clone https://github.com/Mutinda-Mark/Kilimo.git
cd Kilimo
```

Because model checkpoints are managed using Git LFS, ensure Git LFS is installed before retrieving the model files.

```bash
git lfs install
git lfs pull
```

---

## 2. Navigate to the Backend

```bash
cd backend
```

---

## 3. Create a Virtual Environment

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 4. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project uses CPU-compatible PyTorch packages for server deployment.

---

# Environment Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Then configure the required environment variables.

Do not commit real credentials.

---

# Main Backend Environment Variables

The backend uses environment variables including:

```env
DATABASE_URL=

GEMINI_API_KEY=

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=

ADMIN_API_TOKEN=

ENVIRONMENT=development
```

Additional configuration may be documented in:

```text
backend/.env.example
```

The example environment file should be treated as the authoritative list of required backend configuration variables.

---

# Database

KILIMO uses PostgreSQL for persistent application data.

Stored information includes:

- Farmer sessions
- Conversation history
- Disease assessments
- WhatsApp message-processing records
- Multi-image assessment batches
- Accepted batch images
- Disease information
- Knowledge documents
- Retrieval chunks
- Administrative records

Important logical data areas include:

```text
sessions
conversation_history
assessments
whatsapp_messages
whatsapp_assessment_batches
whatsapp_batch_images
disease_info
documents
chunks
admin_users
```

The configured PostgreSQL database must be accessible before the application starts.

---

# Model Weights

Production model checkpoints are managed using **Git LFS**.

The main model paths include:

```text
backend/cv/weights/best_model.pt
backend/cv/weights/tomato_subject_validator.pt
```

The model files must contain the actual binary checkpoints rather than Git LFS pointer files.

If required, retrieve them using:

```bash
git lfs pull
```

---

# Start the Backend Locally

From:

```text
backend/
```

run:

```bash
python -m uvicorn app.main:app --reload
```

The local service normally starts at:

```text
http://127.0.0.1:8000
```

The health endpoint is:

```text
/health
```

---

# Production Endpoint Behaviour

Production deployment is intentionally more restrictive than local development.

Administrative routes are protected.

Development-oriented public prediction and chat endpoints are disabled or restricted in the production environment.

The minimal health endpoint remains available for service monitoring.

---

# Admin Dashboard Setup

Navigate to:

```bash
cd admin-dashboard
```

Install dependencies:

```bash
npm install
```

Create:

```text
.env.local
```

from:

```text
.env.local.example
```

Example server-side configuration includes:

```env
KILIMO_API_URL=http://127.0.0.1:8000
KILIMO_ADMIN_TOKEN=
```

Supabase browser/server configuration is also required for administrator authentication.

Refer to:

```text
.env.local.example
```

for the authoritative variable names.

---

# Start the Admin Dashboard

```bash
npm run dev
```

The dashboard normally starts at:

```text
http://localhost:3000
```

---

# Administrator Authentication

The administrative dashboard uses:

```text
Google OAuth
      |
      v
Supabase Auth
      |
      v
TOTP MFA
      |
      v
AAL2 Session
      |
      v
Admin Registry Check
      |
      v
Protected Dashboard
```

An authenticated Google account alone does not automatically grant dashboard access.

The user must also:

- Complete TOTP MFA
- Reach AAL2
- Exist in the administrator registry
- Be active and authorised

---

# Admin Dashboard Features

The dashboard includes:

- Overview
- Farmer sessions
- Conversation history
- Assessment records
- Individual assessment details
- Model probability information
- Disease distribution analytics
- Severity distribution analytics
- Assessment activity
- Source statistics
- WhatsApp processing information
- Database status
- Model status
- Global search
- Operational notifications
- Administrator profile
- Theme settings
- Manual refresh
- Error handling

---

# WhatsApp Integration

KILIMO integrates with the **Meta WhatsApp Cloud API**.

The processing workflow is:

```text
Incoming Meta Webhook
        |
        v
Signature Verification
        |
        v
Message ID Claim
        |
        v
Duplicate Protection
        |
        v
Immediate HTTP Acknowledgement
        |
        v
Background Processing
        |
        +---------------------+
        |                     |
        v                     v
Text Message              Image Message
        |                     |
        v                     v
Chat / RAG             Quality Validation
                              |
                              v
                       Subject Validation
                              |
                              v
                       Assessment Batch
                              |
                              v
                      Disease Assessment
                              |
                              v
                         Aggregation
        |                     |
        +----------+----------+
                   |
                   v
            Farmer Response
```

Database-backed message claiming protects against duplicate webhook processing.

---

# WhatsApp Security

Incoming Meta webhook requests are validated using the configured WhatsApp application secret.

Webhook signature verification helps ensure that incoming requests originate from the expected Meta integration.

Sensitive values such as:

```text
WHATSAPP_ACCESS_TOKEN
WHATSAPP_APP_SECRET
WHATSAPP_VERIFY_TOKEN
```

must never be committed to Git.

---

# API Security

The backend includes production security controls such as:

- WhatsApp webhook signature validation
- Administrative bearer authentication
- Rate limiting
- Upload-size restrictions
- Generic external error messages
- Production environment validation
- Restricted development endpoints
- Safe application logging
- Server-side administrative credentials

The administrative API token is not exposed to browser-side JavaScript.

---

# Testing

## Backend

Navigate to:

```bash
cd backend
```

Run:

```bash
pytest -q --tb=short
```

Final regression status:

```text
166 passed
3 non-failing warnings
```

The test suite covers areas including:

- API behaviour
- Image quality validation
- Subject validation
- Disease prediction
- Severity processing
- Image compression
- Multi-image aggregation
- Multi-image WhatsApp workflow
- Session management
- Conversation history
- RAG behaviour
- Failure handling
- Duplicate webhook protection
- WhatsApp signature verification
- Upload limits
- Rate limiting
- Administrative authentication
- Production configuration
- Production API restrictions
- Database batch handling
- Model checkpoint validation

---

# Frontend Quality Checks

Navigate to:

```bash
cd admin-dashboard
```

Run:

```bash
npm run lint
```

Then:

```bash
npm run build
```

The production build validates:

- TypeScript compilation
- ESLint rules
- Next.js route generation
- Application bundling
- Production compatibility

---

# Production Deployment

## Backend

The FastAPI backend is deployed to:

```text
Microsoft Azure App Service
```

The production application runs as a Linux/Python service using a single Uvicorn worker.

The single-worker configuration avoids unnecessary duplication of machine-learning models in memory and is compatible with the current process-local application controls.

---

## Dashboard

The administrative dashboard is deployed through:

```text
Vercel
```

The dashboard communicates with the Azure-hosted backend through server-side configuration.

---

# Continuous Deployment

Backend CI/CD is implemented using **GitHub Actions**.

The stable deployment flow is:

```text
Push to main
     |
     v
GitHub Actions
     |
     v
Build
     |
     v
Git LFS Model Retrieval
     |
     v
Azure Authentication using OIDC
     |
     v
Deploy to Azure App Service
```

Azure authentication uses OpenID Connect federation rather than a long-lived Azure password stored in the repository.

---

# Git Workflow

The stable project branch is:

```text
main
```

Sprint and feature work may be developed in separate branches and merged into `main` after testing.

A typical workflow is:

```bash
git status
git add .
git commit -m "Describe the implemented change"
git push
```

Meaningful commit messages should describe the actual change implemented.

---

# Deployment Verification

After deployment, the system should be verified using:

```text
Azure health endpoint
WhatsApp text interaction
Single-image assessment
Multi-image assessment
Unsupported-image rejection
Poor-quality image rejection
Admin dashboard
Database status
Model status
GitHub Actions deployment status
```

During final acceptance testing, the complete deployed workflow operated successfully across:

```text
WhatsApp
→ Meta
→ Azure
→ AI pipeline
→ PostgreSQL
→ Gemini
→ WhatsApp

and

Administrator
→ Vercel
→ Azure Admin API
→ PostgreSQL
```

Under warmed deployment conditions, a typical image interaction produced a farmer-facing response in approximately:

```text
7 seconds
```

This is an observed acceptance-test result rather than a guaranteed service-level response time.

---

# Current Development Status

## Completed

- [x] Tomato disease dataset preparation
- [x] EfficientNet-B0 disease classifier
- [x] MobileNetV3-Large comparison model
- [x] Held-out model evaluation
- [x] Grad-CAM processing
- [x] Severity estimation
- [x] Technical image-quality validation
- [x] MobileNetV3-Small tomato subject validator
- [x] Subject-validator threshold evaluation
- [x] Multi-image assessment
- [x] Prediction aggregation and abstention
- [x] `DONE` batch finalisation
- [x] Stale-batch recovery
- [x] Structured advisory generation
- [x] Retrieval-Augmented Generation
- [x] Context-aware farmer chat
- [x] PostgreSQL session management
- [x] Assessment persistence
- [x] Conversation persistence
- [x] WhatsApp integration
- [x] Duplicate message protection
- [x] Webhook signature verification
- [x] API rate limiting
- [x] Upload controls
- [x] Production endpoint restrictions
- [x] Admin API
- [x] Google OAuth authentication
- [x] TOTP MFA
- [x] Administrator registry authorization
- [x] Administrative dashboard
- [x] Automated backend testing
- [x] Frontend linting
- [x] Frontend production build
- [x] Git LFS model management
- [x] GitHub Actions CI/CD
- [x] Azure backend deployment
- [x] Vercel dashboard deployment
- [x] End-to-end acceptance testing
- [x] Production deployment validation

## Remaining Evaluation Work

- [ ] Formal usability study with representative tomato farmers
- [ ] Larger-scale field evaluation
- [ ] Long-term operational monitoring
- [ ] Large-scale load and concurrency testing

---

# Known Limitations

KILIMO has several important limitations.

- Disease-model performance depends on the representativeness of the training and evaluation datasets.
- Real farmer images may differ substantially from dataset images.
- Lighting, background, camera quality, leaf orientation and disease stage may affect predictions.
- High held-out accuracy does not guarantee equivalent performance on independently collected Kenyan farm images.
- Disease severity is based on Grad-CAM and image-processing heuristics rather than laboratory-validated severity measurement.
- The tomato subject validator cannot guarantee perfect rejection of every unsupported image.
- Multi-image prediction agreement does not guarantee biological correctness.
- The system currently supports tomato conditions only.
- Internet connectivity is required.
- WhatsApp functionality depends on Meta services.
- Natural-language generation depends on Gemini availability.
- Backend hosting depends on Azure.
- Dashboard hosting depends on Vercel.
- Database and authentication services depend on Supabase.
- The agricultural knowledge base may not cover every local farming scenario.
- Formal farmer usability testing remains limited.
- KILIMO is intended as a decision-support tool and does not replace qualified agricultural professionals.

---

# Security and Secret Handling

The following must never be committed to the repository:

- `.env`
- `.env.local`
- Database passwords
- Gemini API keys
- WhatsApp access tokens
- WhatsApp application secrets
- Administrative bearer tokens
- OAuth secrets
- Private keys
- Other production credentials

Example environment files should contain placeholders only.

Model checkpoints are different from secrets and are managed through **Git LFS**.

---

# Responsible AI Use

AI-assisted tools were used during selected development activities such as:

- Code review
- Debugging
- Test refinement
- Deployment troubleshooting
- Documentation drafting
- Technical explanation
- Language improvement

AI-generated suggestions were reviewed against:

- Actual source code
- Automated test results
- Model evaluation output
- Application logs
- Database behaviour
- Deployment evidence
- System screenshots
- Project requirements

Experimental values and final system results were obtained from the project artefacts and execution evidence rather than generated by AI tools.

The student remains responsible for the final implementation, evaluation, interpretation and documentation.

---

# Disclaimer

KILIMO is an agricultural decision-support and farmer advisory system.

Disease predictions, severity estimates and advisory responses should be treated as supporting information rather than guaranteed diagnoses.

Where symptoms are severe, unusual, uncertain or economically significant, farmers should seek assistance from qualified agricultural extension officers, agronomists, plant pathologists or other relevant agricultural professionals.

---

# Academic Documentation

The project documentation covers:

1. Introduction and project background
2. Literature review
3. Methodology
4. System analysis and design
5. System implementation, testing and evaluation
6. Conclusions and recommendations

Implementation claims are supported using:

- Source code
- Git history
- Automated test results
- Model evaluation results
- Deployment logs
- Screenshots
- Database evidence
- Acceptance testing

---

# Author

**Mutuku Mark Mutinda**  
BSc Informatics and Computer Science  
Strathmore University

---

# Supervisor

**Mr. Daniel Machanje**

---

# Project

**KILIMO — Tomato Disease Detection and Farmer Advisory System**

Final-Year Project  
BSc Informatics and Computer Science  
Strathmore University
