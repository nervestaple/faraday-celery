import time
import os

from dotenv import load_dotenv

from celery_app import celery_app

load_dotenv()


@celery_app.task
def get_aosmith_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):

  print(f"### Starting AO Smith Warranty Lookup: {serial_number}")

  load_dotenv()

  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
    text = None
    download = None
    is_dev = os.getenv('ENVIRONMENT') == 'development'
    browser = playwright.chromium.launch(
        headless=(not is_dev), slow_mo=50 if is_dev else 0)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.hotwater.com/support/warranty-verification.html")
    time.sleep(5)
    page.frame_locator('iframe[title="Warranty Verification"]').locator(
        '#MainContent_SerialDetails_txtSerial').click()
    page.frame_locator('iframe[title="Warranty Verification"]').locator(
        '#MainContent_SerialDetails_txtSerial').fill(serial_number)
    page.frame_locator('iframe[title="Warranty Verification"]').locator(
        '#MainContent_SerialDetails_btnSearch').click()
    try:
      page.frame_locator('iframe[title="Warranty Verification"]').get_by_role(
          'heading', name='Unit Details').click()
    except Exception as e:
      print(f"something went wrong: {e}")
