import time
import base64
import os
import requests

from dotenv import load_dotenv
from tempfile import NamedTemporaryFile

from celery_app import celery_app

load_dotenv()

# GET GOODMAN WARRANTY


@celery_app.task
def getGoodmanWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  print(f"### Starting Goodman Warranty Lookup: {serial_number}")

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
    page.goto(
        "https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
    time.sleep(5)
    page.locator("input[name=\"serialNo\"]").click()
    page.locator("input[name=\"serialNo\"]").fill(serial_number)
    page.locator("input[name=\"lastName\"]").click()
    page.locator("input[name=\"lastName\"]").fill(owner_last_name)
    page.get_by_role("button", name="Search").click()
    time.sleep(5)
    try:
      with page.expect_download() as download_info:
        page.get_by_role("button", name="Search").click()
      download = download_info.value
    except Exception as e:
      print(f"something went wrong: {e}")
      is_dev = os.getenv('ENVIRONMENT') == 'development'
      browser = playwright.chromium.launch(
          headless=(not is_dev), slow_mo=50 if is_dev else 0)
      context = browser.new_context()
      page = context.new_page()
      page.goto(
          "https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
      time.sleep(5)
      page.locator("input[name=\"serialNo\"]").click()
      page.locator("input[name=\"serialNo\"]").fill(serial_number)
      page.get_by_role("button", name="Search").click()
      time.sleep(5)
      try:
        with page.expect_download() as download_info:
          page.get_by_role("button", name="Search").click()
        download = download_info.value
      except Exception as e:
        print(f"something went wrong: {e}")

    if download is not (None):
      temp_file = NamedTemporaryFile(delete=True)
      download.save_as(temp_file.name)
      temp_file.flush()

      # ---------------------
      context.close()
      browser.close()
      return {"text": None, "pdf": temp_file}

    context.close()
    browser.close()
    return None

  pdf = None
  with sync_playwright() as playwright:
    result = run(playwright)
    if result is not (None):
      pdf = result["pdf"]

  encoded_pdf = None
  if pdf is not (None):
    with open(pdf.name, "rb") as pdf:
      encoded_pdf = base64.b64encode(pdf.read()).decode('ascii')

  if int(instant) == 1:
    return {"filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": None, "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": None, "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)
