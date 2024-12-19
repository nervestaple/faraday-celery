import json
import requests
import re

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as dateparse
from dotenv import load_dotenv
from playwright.sync_api import Page

from celery_app import celery_app
from scrape import scrape
import base64

load_dotenv()

# for future ref: check bradford white reg: https://warrantycenter.bradfordwhite.com/warranty/registrations-warranty/SC41081284


@celery_app.task
def get_bradford_white_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  def get_warranty_object(page: Page):
    page.goto('https://warrantycenter.bradfordwhite.com/')
    page.locator("#check_serial_number").click()
    page.locator("#check_serial_number").fill(serial_number)
    page.locator("#check_btn").click()
    page.wait_for_load_state('networkidle')

    error_texts = page.locator('.alert.alert-danger').all_inner_texts()
    filtered_error_texts = [text.replace('×', '').strip()
                            for text in error_texts if text]
    error_text = '\n'.join([text for text in filtered_error_texts if text])
    if len(filtered_error_texts) > 0:
      print(f'Error with serial {serial_number}:', error_text)
      return None, None

    page.pause()

    page.locator('.warranty-body').click()
    cells = page.locator('.warranty-body').locator('tr td:nth-child(3)').all()
    cell_data = [cell.text_content().strip() for cell in cells]
    print('cell_data:', cell_data)
    if len(cell_data) < 8:
      return None, None

    serial, model, heater_type, mfg_date_str, original_mfg_date_str, warranty_length, warranty_expire_date_str, registration_status, *rest = cell_data
    registration_date_str = None
    if len(rest) > 0:
      registration_date_str = rest[0]

    mfg_date = dateparse(mfg_date_str)

    warranty_expire_date = None
    install_date = None
    registration_date = None

    try:
      match = re.match(r'^Tank - (.+), Parts - (.+)$',
                       warranty_expire_date_str)
      if match:
        tank_expire_date = match.group(1)
        parts_expire_date = match.group(2)
        print('Tank:', tank_expire_date, 'Parts:', parts_expire_date)
        warranty_expire_date = dateparse(tank_expire_date)
      else:
        warranty_expire_date = dateparse(
          warranty_expire_date_str.replace('*', ''))

      install_date = (warranty_expire_date -
                      relativedelta(years=6)).timestamp()
    except Exception as e:
      print('Error parsing warranty expire date:', e)

    try:
      registration_date = dateparse(registration_date_str)
    except Exception as e:
      print('Error parsing registration date:', e)

    pdf_bytes = page.pdf()
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    return pdf_base64, {
      "certificate": None,
      "install_date": install_date,
      "is_registered": registration_status == 'Registered',
      "last_name_match": False,
      "manufacture_date": mfg_date.timestamp(),
      "model_number": model,
      "register_date": registration_date.timestamp() if registration_date else None,
      "shipped_date": None,
      "warranties": [
          {
              "end_date": warranty_expire_date.timestamp() if warranty_expire_date else None,
              "name": "Glass Lined Tank and Parts",
              "start_date": install_date
          }
      ]
    }

  pdf_base64, warranty_object = scrape(get_warranty_object)

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": pdf_base64}

  print({
      "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id})

  body = {
    "warranty_object": json.dumps(warranty_object),
    "filedata": pdf_base64
  }

  if equipment_scan_id:
    body["equipment_scan_id"] = equipment_scan_id
  elif equipment_id:
    body["equipment_id"] = equipment_id

  r = requests.post(
    'https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data=body, timeout=30)
  print(r)
