import os
import signal

from celery import Celery
from dotenv import load_dotenv
from celery.utils.log import get_task_logger
from contextlib import contextmanager

load_dotenv()

celery_app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
celery_logger = get_task_logger(__name__)

celery_app.autodiscover_tasks(
  ['tasks', 'tasks.warranty_lookup'],
  force=True
)


class TimeoutException(Exception):
  pass


@contextmanager
def time_limit(seconds):
  def signal_handler(signum, frame):
    raise TimeoutException("Timed out!")
  signal.signal(signal.SIGALRM, signal_handler)
  signal.alarm(seconds)
  try:
    yield
  finally:
    signal.alarm(0)
