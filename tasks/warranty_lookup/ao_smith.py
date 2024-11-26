import time
from playwright.sync_api import Page

from celery_app import celery_app
from scrape import scrape


@celery_app.task
def get_aosmith_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):

  print(f"### Starting AO Smith Warranty Lookup: {serial_number}")

  def scraper(page: Page):
    text = None
    download = None
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

  scrape(scraper)
