# Tomato disease advisory backend - Phase 0 skeleton

A WhatsApp-based farmer support platform for tomato disease detection
(CNN + Grad-CAM) and agricultural advisory (RAG over PostgreSQL/pgvector).
See the project PRD for full requirements.

This Phase 0 skeleton sets up the foundations: a FastAPI app with a
healthcheck endpoint, a Postgres+pgvector database, and a background
task queue - all running natively on Windows with no Docker and no Redis.

## Stack

| Component                  | Choice                                   |
|-----------------------------|------------------------------------------|
| API framework                | FastAPI + Uvicorn                       |
| Database                     | Supabase Postgres (pgvector enabled)    |
| Sessions & conversation log   | PostgreSQL tables (no Redis)            |
| Background task queue        | Huey (SQLite broker, thread workers)    |
| CV model                      | PyTorch + grad-cam (trained on Colab)   |
| RAG embeddings & generation   | OpenAI API                               |
| WhatsApp integration          | Meta WhatsApp Cloud API (Phase 6)        |

## 1. Set up the database (Supabase)

1. Create a free account at https://supabase.com and create a new project.
2. In the project dashboard, go to **Project Settings > Database** and
   copy the connection string under **Connection string (URI)**. It looks
   like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
3. Open the **SQL Editor** in Supabase, paste the contents of
   `db/schema.sql`, and run it. This enables pgvector and creates all the
   tables needed for Phases 3, 5, and 7.

## 2. Set up the Python environment (Windows)

```powershell
# From the project root
python -m venv .venv
.venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

If `torch`/`torchvision` are slow to install or you hit wheel issues,
install them first from the official index, then install the rest:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

(CPU-only is fine for local inference - training happens on Colab's GPU
in Phase 1/2, and you'll just download the resulting weights here.)

## 3. Configure environment variables

```powershell
copy .env.example .env
```

Edit `.env` and paste in your Supabase `DATABASE_URL`. The OpenAI and
WhatsApp values can stay empty for now - they're needed starting Phase 3
and Phase 6 respectively.

## 4. Run the API

```powershell
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/health in a browser. You should see:

```json
{"status": "ok", "database": "connected", "environment": "development"}
```

If `database` says `"unreachable"`, double-check the `DATABASE_URL` in
`.env` (a common mistake is leaving the literal `[YOUR-PASSWORD]` /
`[YOUR-PROJECT-REF]` placeholders in place).

## 5. Run the background task consumer

In a second terminal (with the same virtual environment activated):

```powershell
huey_consumer app.tasks.huey -k thread -w 4
```

This starts the Huey consumer using 4 thread-based workers - no Redis or
separate broker process required. It currently has nothing to do (Phase 7
will add the real diagnosis/RAG tasks), but this confirms the setup works.

## 6. Run the tests

```powershell
pytest
```

Both tests should pass even without `.env` configured, since `/health`
reports `"degraded"` instead of crashing when the database isn't reachable.

## Project layout

```
tomato_advisory_backend/
├── app/
│   ├── main.py        # FastAPI app + healthcheck
│   ├── config.py      # Settings loaded from .env
│   ├── db.py           # Postgres/pgvector connection pool
│   └── tasks.py        # Huey background task queue
├── cv/                  # Phase 1/2: CNN classifier + Grad-CAM severity
├── nlp/                 # Phase 3/4: RAG pipeline + multilingual layer
├── db/
│   └── schema.sql       # Run this once against Supabase
├── tests/
├── requirements.txt
└── .env.example
```

## What's next (Phase 1)

Train the CNN disease classifier on the Kaggle tomato-disease-multiple-sources
dataset in Google Colab, evaluate against the >90% accuracy target, and
export the model so it can be loaded by `cv/` for local inference.
