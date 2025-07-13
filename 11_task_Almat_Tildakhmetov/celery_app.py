from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery = Celery(
    "celery_app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL
)

@celery.task
def send_email_task(email: str):
    import time
    time.sleep(5)  # имитация долгой отправки
    print(f"Email sent to {email}")
    return f"Email sent to {email}"
