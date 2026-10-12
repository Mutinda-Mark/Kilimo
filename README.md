# KILIMO — Tomato Disease Detection and Farmer Advisory System

KILIMO is a smartphone-based farmer advisory system for tomato disease detection using computer vision and natural language processing.

The system allows tomato farmers to interact through **WhatsApp** by sending tomato leaf images, text questions, or both. Submitted images are processed by a trained deep learning model to identify the likely tomato disease, estimate disease severity, and generate farmer-friendly advisory information.

The system also supports contextual follow-up questions using a **Retrieval-Augmented Generation (RAG)** pipeline.

An administrative dashboard is included for monitoring farmer sessions, disease assessments, conversations, analytics, WhatsApp processing, and overall system activity.

---

## Project Overview

KILIMO was developed as a final-year **BSc Informatics and Computer Science** project at **Strathmore University**.

The system combines:

- Computer Vision for tomato disease classification
- EfficientNet-B0 transfer learning
- Grad-CAM-based image interpretation
- Disease severity estimation
- Retrieval-Augmented Generation (RAG)
- Natural language response generation
- WhatsApp Cloud API integration
- PostgreSQL data persistence
- FastAPI backend services
- Next.js administrative dashboard

---

## Core Workflow

The main farmer workflow is:

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
Image / Text Processing
  |
  +---------------------------+
  |                           |
  v                           v
Computer Vision           NLP / RAG
  |                           |
  v                           v
Disease Prediction       Advisory Context
  |                           |
  +-------------+-------------+
                |
                v
        Farmer Advisory Response
                |
                v
             WhatsApp
```

Assessment results, conversations, farmer sessions, and system events are stored in PostgreSQL and can be monitored through the administrative dashboard.

---

## Supported Tomato Classes

The computer vision model currently supports **11 classes**:

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

## Computer Vision Model

The image classification component uses **EfficientNet-B0** with transfer learning.

Training was performed in two main phases:

- **Phase A — Initial Training**
- **Phase B — Fine-Tuning**

The highest validation accuracy recorded during model development was approximately:

```text
98.79%
```

> **Note:** This value represents validation performance during model development and should not be interpreted as final held-out test accuracy.

The trained model weights are not stored directly in this Git repository.

---

## Project Structure

```text
Kilimo/
|
├── backend/
│   ├── app/
│   │   ├── admin/
│   │   ├── services/
│   │   └── whatsapp/
│   │
│   ├── cv/
│   │   ├── assessor.py
│   │   ├── config.py
│   │   ├── gradcam.py
│   │   ├── model.py
│   │   ├── predictor.py
│   │   ├── segmentation.py
│   │   ├── severity.py
│   │   └── train_colab.ipynb
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
│   └── .env.example
│
├── admin-dashboard/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── lib/
│   │
│   ├── public/
│   ├── package.json
│   └── .env.local.example
│
├── .gitignore
└── README.md
```

---

## Main Technologies

### Backend

- Python
- FastAPI
- PostgreSQL
- asyncpg
- PyTorch
- torchvision
- Pillow
- Google Gemini API
- Meta WhatsApp Cloud API

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts

### Development and Testing

- pytest
- pytest-asyncio
- ESLint
- Git
- GitHub
- Google Colab
- Visual Studio Code

---

## Backend Setup

### 1. Navigate to the Backend

```bash
cd backend
```

### 2. Create a Python Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

#### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
.venv\Scripts\activate
```

#### Linux / macOS

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Create the Environment File

Copy:

```text
.env.example
```

to:

```text
.env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

On Linux or macOS:

```bash
cp .env.example .env
```

Then fill in the required environment variables.

> **Important:** Never commit the `.env` file or real credentials to Git.

---

## Required Backend Environment Variables

The backend requires configuration similar to the following:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

GEMINI_API_KEY=

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
WHATSAPP_API_VERSION=

ADMIN_API_TOKEN=
```

Real secrets must never be committed to Git or included in public documentation.

---

## PostgreSQL

KILIMO uses PostgreSQL for storing application data including:

- Farmer sessions
- Conversation history
- Disease assessments
- WhatsApp message processing records
- Disease information
- Knowledge documents
- Retrieval chunks
- System activity records

Main database tables include:

```text
sessions
conversation_history
assessments
whatsapp_messages
disease_info
documents
chunks
```

The PostgreSQL database must be running and accessible before starting the backend application.

---

## Model Weights

The trained EfficientNet-B0 model weights are expected at:

```text
backend/cv/weights/best_model.pt
```

The weights are intentionally excluded from Git because trained model files may be large and should be managed separately.

The deployment or development environment must therefore supply the trained model file before image prediction can be performed.

---

## Start the Backend

From the `backend` directory, run:

```bash
uvicorn app.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

Useful development endpoints include:

```text
/
 /health
 /predict
 /chat
 /webhook/whatsapp
```

Administrative endpoints are available under:

```text
/admin/
```

Administrative routes require a valid administrative bearer token.

---

## Admin Dashboard Setup

Navigate to the dashboard directory:

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

using:

```text
.env.local.example
```

Example configuration:

```env
KILIMO_API_URL=http://127.0.0.1:8000
KILIMO_ADMIN_TOKEN=
```

The administrative token must match the `ADMIN_API_TOKEN` configured in the backend.

---

## Start the Admin Dashboard

Run:

```bash
npm run dev
```

The dashboard will normally be available at:

```text
http://localhost:3000
```

---

## Admin Dashboard Features

The administrative dashboard currently provides:

- System overview
- Farmer session monitoring
- Conversation history
- Disease assessment records
- Individual assessment details
- Disease distribution statistics
- Severity statistics
- Assessment activity analytics
- Data source statistics
- WhatsApp processing status
- Database monitoring
- Model information

---

## WhatsApp Integration

KILIMO integrates with the **Meta WhatsApp Cloud API**.

The current WhatsApp processing workflow is:

```text
WhatsApp Message
      |
      v
Meta WhatsApp Cloud API
      |
      v
FastAPI Webhook
      |
      v
Message ID Validation
      |
      v
Database Duplicate Check
      |
      v
Background Processing
      |
      +------------------+
      |                  |
      v                  v
Text Processing       Image Processing
      |                  |
      v                  v
NLP / RAG          CV Assessment
      |                  |
      +--------+---------+
               |
               v
       WhatsApp Response
```

Incoming Meta message IDs are stored in the database to prevent the same message from being processed more than once.

This duplicate-message protection helps prevent repeated advisory responses when webhook events are delivered multiple times.

---

## Computer Vision Pipeline

The computer vision pipeline performs several stages of image analysis.

A simplified workflow is:

```text
Farmer Image
     |
     v
Image Validation
     |
     v
Image Preprocessing
     |
     v
EfficientNet-B0
     |
     v
Disease Classification
     |
     v
Grad-CAM
     |
     v
Severity Estimation
     |
     v
Assessment Result
```

The image assessment may include:

- Predicted disease class
- Prediction confidence
- Grad-CAM visualization information
- Estimated severity
- Structured disease information
- Recommended farmer actions

---

## Disease Severity Estimation

Disease severity is estimated using image analysis and Grad-CAM-related heuristics.

The severity component helps provide farmers with an approximate indication of how significant the detected symptoms appear within the submitted image.

Severity estimation should be interpreted as an advisory estimate rather than a laboratory-confirmed measurement.

---

## RAG and Natural Language Advisory

The advisory pipeline combines:

- Structured disease information
- Semantic retrieval
- Farmer question context
- Previous assessment context
- Recent conversation history
- Google Gemini response generation

The purpose of the RAG pipeline is to generate contextual responses grounded in available agricultural knowledge.

This allows a farmer to ask follow-up questions such as:

```text
What should I do about it?

How can I prevent it from spreading?

Is the condition serious?

What treatment should I use?

Can it affect the rest of my tomatoes?
```

The farmer does not need to repeat the disease name after every message because previous assessment and conversation context can be retrieved from the active session.

---

## Farmer Conversation Flow

A typical interaction may look like:

```text
Farmer:
[Uploads tomato leaf image]

KILIMO:
The image appears most consistent with Early Blight.
Estimated severity: Moderate.

Recommended action:
Remove heavily affected leaves, avoid overhead watering,
and monitor nearby plants for additional symptoms.

Farmer:
How can I prevent it from spreading?

KILIMO:
Provides a contextual response using the previous
Early Blight assessment and retrieved advisory knowledge.
```

---

## Testing

### Backend Tests

Navigate to the backend:

```bash
cd backend
```

Run:

```bash
pytest -v
```

The automated test suite covers areas including:

- API health checks
- Image validation
- Disease prediction
- Severity processing
- Advisory generation
- RAG retrieval
- Farmer session handling
- Conversation flow
- Failure handling
- WhatsApp webhook processing
- Duplicate message protection

---

## Frontend Quality Checks

Navigate to the admin dashboard:

```bash
cd admin-dashboard
```

Run linting:

```bash
npm run lint
```

Then create a production build:

```bash
npm run build
```

The production build helps verify:

- TypeScript compilation
- ESLint checks
- Next.js route generation
- Partial prerendering
- Production compatibility

---

## Security and Secret Handling

The following are intentionally excluded from version control:

- `.env`
- `.env.local`
- API credentials
- WhatsApp access tokens
- Gemini API keys
- Administrative API tokens
- PostgreSQL passwords
- Model weight files
- Private keys
- Python virtual environments
- Node.js dependencies
- Next.js build output

Example environment files contain placeholders only.

Sensitive credentials should never be added directly to source code or committed to the Git repository.

---

## Known Current Limitations

The current prototype has several limitations:

- Disease classification performance depends on the representativeness of the training dataset.
- Real-world farmer images may differ significantly from controlled dataset images.
- Lighting, camera quality, leaf orientation, background clutter, and disease stage may affect predictions.
- Severity estimation is based on image and Grad-CAM heuristics and is not a laboratory-confirmed measurement.
- The system currently focuses only on tomato-related conditions.
- Internet connectivity is required for WhatsApp communication and external AI services.
- The advisory knowledge base may not cover every local farming condition.
- Natural language responses depend on the quality of retrieved knowledge and available conversational context.
- The system is intended as a farmer-support tool and does not replace qualified agricultural experts.
- Final production deployment and comprehensive field evaluation are still in progress.

---

## Current Development Status

### Completed

- [x] Computer vision model
- [x] Disease classification
- [x] EfficientNet-B0 transfer learning
- [x] Grad-CAM processing
- [x] Severity estimation
- [x] Structured advisory generation
- [x] RAG pipeline
- [x] Contextual chat
- [x] PostgreSQL session management
- [x] Assessment persistence
- [x] Conversation persistence
- [x] WhatsApp integration
- [x] Duplicate message protection
- [x] Admin API
- [x] Admin dashboard
- [x] Automated backend testing
- [x] Frontend linting
- [x] Production build validation

### In Progress

- [ ] Security hardening
- [ ] Final model evaluation
- [ ] Production deployment
- [ ] Usability evaluation
- [ ] Final documentation
- [ ] End-to-end acceptance testing

---

## Git Workflow

Development is maintained using **Git** and **GitHub**.

The current repository baseline was created after the initial local prototype had already been implemented.

Changes from this point onward should be committed using clear and meaningful commit messages.

Examples:

```text
Add webhook signature verification

Add final model evaluation results

Harden session history access

Add production deployment configuration

Update Chapter 5 implementation evidence
```

A typical workflow is:

```bash
git status

git add .

git commit -m "Describe the implemented change"

git push
```

---

## Project Documentation

The academic project documentation covers:

1. Project background
2. Problem statement
3. Project objectives
4. Literature review
5. Research and development methodology
6. System analysis and design
7. System implementation
8. Testing and evaluation
9. Conclusions and recommendations

Implementation documentation is being maintained alongside system development so that claims in the academic report can be supported by actual source code, test results, screenshots, model results, and system evidence.

---

## Responsible AI Use

AI-assisted tools may be used during development for activities such as:

- Code review
- Debugging
- Test refinement
- Documentation drafting
- Language improvement
- Explanations of technical concepts

Any material produced with AI assistance should be reviewed against:

- The actual project source code
- Test results
- Model evaluation results
- Database evidence
- System screenshots
- Project requirements
- Credible academic and technical references

The student remains responsible for the final implementation, analysis, interpretation, documentation, and submitted work.

---

## Disclaimer

KILIMO is designed as an agricultural decision-support and farmer advisory system.

Predictions and recommendations produced by the system should be treated as advisory information rather than a guaranteed diagnosis.

Where symptoms are severe, unusual, uncertain, or economically significant, farmers should seek assistance from qualified agricultural extension officers, agronomists, plant pathologists, or other relevant agricultural professionals.

---

## Author

**Mutuku Mark Mutinda**  
BSc Informatics and Computer Science  
Strathmore University

---

## Supervisor

**Mr. Daniel Machanje**

---

## Project

**KILIMO — Tomato Disease Detection and Farmer Advisory System**

Final-Year Project  
BSc Informatics and Computer Science  
Strathmore University