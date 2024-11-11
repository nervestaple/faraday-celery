import time

from dotenv import load_dotenv
from time import sleep

from celery_app import celery_app
from tasks.identify_new_model import *

load_dotenv()


@celery_app.task
def manual_lookup(model_number, manufacturer, equipment_type, model_id):
  load_dotenv()
  return model_number


@celery_app.task
def test_task():
  print("TEST_TASK STARTING")
  sleep(5)
  print("TEST_TASK COMPLETED")
  return time.time()


@celery_app.task
def sum_test_task(a, b):
  sleep(5)
  print("sum test task completed")
  return a + b
