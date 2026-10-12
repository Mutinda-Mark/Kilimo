"""
Background task queue.

Replaces Celery+Redis with Huey backed by a local SQLite file. This needs
no separate broker process and runs cleanly on Windows when the consumer
is started with the thread worker pool:

    huey_consumer app.tasks.huey -k thread -w 4

Phase 7 will add the real tasks here (run CV inference, run the RAG
pipeline, send the WhatsApp reply). For now there's just a placeholder
task to confirm the consumer is wired up correctly.
"""

from huey import SqliteHuey

from app.config import settings

huey = SqliteHuey(filename=settings.huey_db_path)


@huey.task()
def example_ping_task(message: str) -> str:
    """Placeholder task - returns a pong so we can confirm the consumer works."""
    return f"pong: {message}"
