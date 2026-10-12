# KILIMO — Tomato Disease Detection and Farmer Advisory System

KILIMO is a smartphone-based farmer advisory system for tomato disease detection using computer vision and natural language processing.

The system allows tomato farmers to interact through WhatsApp by sending tomato leaf images, text questions, or both. Submitted images are processed by a trained deep learning model to identify the likely tomato disease, estimate disease severity, and generate farmer-friendly advisory information. The system also supports contextual follow-up questions using a retrieval-augmented natural language pipeline.

An administrative dashboard is included for monitoring farmer sessions, assessments, analytics, and system activity.

---

## Project Overview

KILIMO was developed as a final-year Informatics and Computer Science project.

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

Assessment results, conversations, and system events are stored in PostgreSQL and are available through the administrative dashboard.

```text

---

## Supported Tomato Classes

The computer vision model currently supports 11 classes:
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

## Model

The image classification component uses EfficientNet-B0 with transfer learning.
Training was performed in two phases:
- Phase A — initial training
- Phase B — fine-tuning
The highest validation accuracy recorded during model development was approximately:
98.79%

This value represents validation performance and should not be interpreted as final held-out test accuracy.
The trained model weights are not stored directly in this Git repository.

---

## Project Structure

```text
Kilimo/
|
├── backend/
|   ├── app/
|   |   ├── admin/
|   |   ├── services/
|   |   └── whatsapp/
|   |
|   ├── cv/
|   |   ├── assessor.py
|   |   ├── config.py
|   |   ├── gradcam.py
|   |   ├── model.py
|   |   ├── predictor.py
|   |   ├── segmentation.py
|   |   ├── severity.py
|   |   └── train_colab.ipynb
|   |
|   ├── nlp/
|   |   ├── advisory.py
|   |   ├── embeddings.py
|   |   ├── knowledge.py
|   |   ├── rag.py
|   |   ├── responder.py
|   |   └── seed_knowledge.py
|   |
|   ├── tests/
|   ├── requirements.txt
|   └── .env.example
|
├── admin-dashboard/
|   ├── src/
|   |   ├── app/
|   |   ├── components/
|   |   ├── hooks/
|   |   └── lib/
|   |
|   ├── public/
|   ├── package.json
|   └── .env.local.example
|
├── .gitignore
└── README.md

---

## Main Technologies

## Backend
- Python
- FastAPI
- PostgreSQL
- asyncpg
- PyTorch
- torchvision
- Pillow
- Google Gemini API
- Meta WhatsApp Cloud API

## Frontend
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts

## Development and Testing
- pytest
- pytest-asyncio
- ESLint
- Git
- GitHub
- Google Colab
- Visual Studio Code

Backend Setup
1. Navigate to the backend
cd backend

2. Create a Python virtual environment
python -m venv .venv

3. Activate it
Windows PowerShell:
.\.venv\Scripts\Activate.ps1

4. Install dependencies
pip install -r requirements.txt

5. Create the environment file
Copy:
.env.example

to:
.env

Example:
Copy-Item .env.example .env

Then fill in the required environment variables.
Do not commit the .env file.

Required Backend Environment Variables
The backend requires configuration similar to:
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

GEMINI_API_KEY=

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
WHATSAPP_API_VERSION=

ADMIN_API_TOKEN=

Real secrets must never be committed to Git.
PostgreSQL
KILIMO uses PostgreSQL for:
- farmer sessions
- conversation history
- disease assessments
- WhatsApp message processing records
- disease knowledge and retrieval data
Main tables include:
sessions
conversation_history
assessments
whatsapp_messages
disease_info
documents / chunks

The database must be available before starting the backend.
Model Weights
The trained EfficientNet-B0 model weights are expected at:
backend/cv/weights/best_model.pt

The weights are intentionally excluded from Git.
The deployment or development environment must supply the trained model separately.
Start the Backend
From the backend directory:
uvicorn app.main:app --reload

The API will normally be available at:
http://127.0.0.1:8000

Useful development endpoints include:
/
 /health
 /predict
 /chat
 /webhook/whatsapp

Administrative endpoints are available under:
/admin/

and require an administrative bearer token.
Admin Dashboard Setup
Navigate to:
cd admin-dashboard

Install dependencies:
npm install

Create:
.env.local

using:
.env.local.example

Example configuration:
KILIMO_API_URL=http://127.0.0.1:8000
KILIMO_ADMIN_TOKEN=

The administrative token must match the backend configuration.
Start the Admin Dashboard
npm run dev

The dashboard is normally available at:
http://localhost:3000

Admin Dashboard Features
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
WhatsApp Integration
KILIMO integrates with the Meta WhatsApp Cloud API.
The current workflow is:
WhatsApp message
      |
      v
Meta Cloud API
      |
      v
FastAPI webhook
      |
      v
Message ID validation
      |
      v
Database duplicate check
      |
      v
Background processing
      |
      +------------------+
      |                  |
      v                  v
Text processing       Image processing
      |                  |
      v                  v
NLP / RAG          CV assessment
      |                  |
      +--------+---------+
               |
               v
       WhatsApp response

Incoming Meta message IDs are stored to prevent the same message from being processed more than once.
RAG and Natural Language Advisory
The advisory pipeline combines:
- structured disease information
- semantic retrieval
- farmer question context
- previous assessment context
- recent conversation history
- Gemini response generation
This allows a farmer to ask contextual questions such as:
What should I do about it?
How can I prevent it from spreading?
Is the condition serious?

without repeating the full disease information.
Testing
Backend
Run:
cd backend
pytest -v

The automated suite covers areas including:
- API health checks
- image validation
- disease prediction
- severity processing
- advisory generation
- RAG retrieval
- session handling
- conversation flow
- failure handling
- WhatsApp webhook processing
- duplicate message protection
Frontend Quality Checks
Run:
cd admin-dashboard
npm run lint

Then:
npm run build

The production build verifies:
- TypeScript compilation
- ESLint checks
- Next.js route generation
- partial prerendering
- production compatibility
Security and Secret Handling
The following are intentionally excluded from version control:
- .env
- .env.local
- API credentials
- WhatsApp access tokens
- Gemini API keys
- administrative API tokens
- PostgreSQL passwords
- model weight files
- private keys
- virtual environments
- Node.js dependencies
- Next.js build output
Example environment files contain placeholders only.

Known Current Limitations
The current prototype has several limitations:
- Disease classification depends on the representativeness of the training dataset.
- Real-world farmer images may differ from controlled dataset images.
- Severity estimation is based on image and Grad-CAM heuristics and is not a laboratory-confirmed measurement.
- The system currently focuses only on tomato-related conditions.
- Internet connectivity is required for WhatsApp and external AI services.
- The advisory knowledge base may not cover every local farming condition.
- The system is a farmer-support tool and does not replace qualified agricultural experts.
- Final deployment and comprehensive field evaluation are still in progress.
Current Development Status
Completed
- Computer vision model
- Disease classification
- Grad-CAM processing
- Severity estimation
- Structured advisory generation
- RAG pipeline
- Contextual chat
- PostgreSQL session management
- Assessment persistence
- WhatsApp integration
- Duplicate message protection
- Admin API
- Admin dashboard
- Automated backend testing
- Frontend linting and production build validation
In Progress
- Security hardening
- Final model evaluation
- Production deployment
- Usability evaluation
- Final documentation
- End-to-end acceptance testing
Git Workflow
Development is maintained using Git and GitHub.
The current repository baseline was created after the initial local prototype had been implemented.
Changes from this point onward should be committed using meaningful messages such as:
Add webhook signature verification
Add final model evaluation results
Harden session history access
Add production deployment configuration
Update Chapter 5 implementation evidence

Project Documentation
The academic documentation covers:
- project background
- problem statement
- objectives
- literature review
- methodology
- system analysis and design
- system implementation
- testing and evaluation
The implementation documentation is being maintained alongside development.
Responsible AI Use
AI-assisted tools may be used during development for activities such as:
- code review
- debugging
- test refinement
- documentation drafting
- language improvement
Any material AI-assisted work should be reviewed against the source code, test results, project evidence, and credible references before being included in the final project documentation.
The student remains responsible for the final implementation, analysis, interpretation, and submitted work.
Author
Mutuku Mark Mutinda
BSc Informatics and Computer Science
Strathmore University
Supervisor
Mr. Daniel Machanje