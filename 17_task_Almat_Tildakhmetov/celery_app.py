from celery import Celery
from config import settings

CELERY_BROKER_URL = settings.CELERY_BROKER_URL

celery = Celery(
    "celery_app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL
)

@celery.task
def send_email_task(email: str):
    import time
    time.sleep(5)
    print(f"Email sent to {email}")
    return f"Email sent to {email}"
