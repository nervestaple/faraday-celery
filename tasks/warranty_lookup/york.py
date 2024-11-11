import time
import base64
import json
import os
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile

from celery_app import celery_app

load_dotenv()


@celery_app.task
def get_york_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  print(f"### Starting York Warranty Lookup: {serial_number}")

  load_dotenv()

  from playwright.sync_api import Playwright, sync_playwright

  def run(playwright: Playwright) -> None:
    html = None
    download = None
    pdf = None
    is_dev = os.getenv('ENVIRONMENT') == 'development'
    browser = playwright.chromium.launch(
        headless=(not is_dev), slow_mo=50 if is_dev else 0)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.yorknow.com/warranty-tools")
    page.query_selector("#warrantysearch").click()
    page.query_selector("#warrantysearch").fill(serial_number)
    # print(page.query_selector("#warrantysearch"))
    # print(page.get_by_role("button", name="Lookup Warranty"))
    page.get_by_role("button", name="Lookup Warranty").click()
    time.sleep(10)
    # print(page.query_selector(".details-title"))
    page.query_selector(".details-title").click()
    html = page.query_selector("#warranty-details").inner_html()
    try:
      with page.expect_download() as download_info:
        page.get_by_role(
            'button', name='Download Warranty Certificate').click()
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
      return {"html": html, "pdf": temp_file}
    else:
      context.close()
      browser.close()
      return None

  with sync_playwright() as playwright:
    result = run(playwright)
    html = result["html"]
    pdf = result["pdf"]

  soup = BeautifulSoup(html, "html.parser")

  if soup.select_one('div:-soup-contains("Warranty Unit Details")'):

    warranty_object = {}
    warranty_object["is_registered"] = False
    warranty_object["shipped_date"] = None
    warranty_object["install_date"] = None
    warranty_object["register_date"] = None
    warranty_object["manufacture_date"] = None
    warranty_object["last_name_match"] = False
    warranty_object["certificate"] = None

    # GET MODEL NUMBER
    warranty_unit_details = soup.select_one(".details-content-row")
    # print(warranty_unit_details)
    rows = warranty_unit_details.findAll('div')
    # print(rows)
    model_number = rows[1].get_text().strip()
    print(f"model number: {model_number}")
    warranty_object["model_number"] = model_number

    # GET REGISTER STATUS
    register_status = rows[3].get_text().strip()
    if register_status == "Product registered":
      warranty_object["is_registered"] = True

    # GET INSTALL DATE
    latest_date = soup.find(
        'div', text="Latest Date On Record:").find_next('div')
    # print(latest_date)
    latest_date = latest_date.get_text().strip()
    # print(latest_date)
    latest_date = time.mktime(datetime.strptime(
        latest_date, "%m/%d/%Y").timetuple())
    print(f"latest date: {latest_date}")
    warranty_object["install_date"] = int(latest_date)

    # GET INDIVIDUAL WARRANTIES
    warranties = []
    warranty_table = soup.select_one("#warranty-coverage-table")
    print(warranty_table)
    warranty_rows = warranty_table.findAll(
        "div", class_="details-content-row")
    print(warranty_rows)
    for warranty_row in warranty_rows:
      print(warranty_row)
      warranty_details = {}
      warranty_fields = warranty_row.findAll('div')
      name = warranty_fields[0].get_text().strip()
      warranty_details["name"] = name

      end_date = warranty_fields[2].get_text().strip()
      end_date = time.mktime(datetime.strptime(
          end_date, "%m/%d/%Y").timetuple())
      warranty_details["end_date"] = int(end_date)
      warranty_details["start_date"] = int(latest_date)
      warranty_details["type"] = "Standard"
      warranties.append(warranty_details)
    warranty_object["warranties"] = warranties

  else:
    warranty_object = None

  print(warranty_object)
  encoded_pdf = None
  if pdf is not (None):
    with open(pdf.name, "rb") as pdf:
      encoded_pdf = base64.b64encode(pdf.read()).decode('ascii')

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)
