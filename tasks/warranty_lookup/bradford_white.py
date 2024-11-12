import json
import requests

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as dateparse
from dotenv import load_dotenv

from celery_app import celery_app

load_dotenv()

# for future ref: check bradford white reg: https://warrantycenter.bradfordwhite.com/warranty/registrations-warranty/SC41081284


@celery_app.task
def get_bradford_white_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  def get_warranty_object(page):
    page.goto('https://warrantycenter.bradfordwhite.com/')
    page.locator("#check_serial_number").click()
    page.locator("#check_serial_number").fill(serial_number)
    page.locator("#check_btn").click()
    page.locator('.warranty-body').click()
    cells = page.locator('.warranty-body').locator('tr td:nth-child(3)').all()
    cell_data = [cell.text_content().strip() for cell in cells]
    if len(cell_data) < 8:
      return None

    serial, model, heater_type, mfg_date_str, original_mfg_date_str, warranty_length, warranty_expire_date_str, registration_status = cell_data

    mfg_date = dateparse(mfg_date_str)
    warranty_expire_date = dateparse(warranty_expire_date_str.replace('*', ''))
    install_date = (warranty_expire_date - relativedelta(years=6)).timestamp()

    return {
      "certificate": None,
      "install_date": install_date,
      "is_registered": registration_status != 'Not Registered',
      "last_name_match": False,
      "manufacture_date": mfg_date.timestamp(),
      "model_number": model,
      "register_date": None,
      "shipped_date": None,
      "warranties": [
          {
              "end_date": warranty_expire_date.timestamp(),
              "name": "Glass Lined Tank and Parts",
              "start_date": install_date
          }
      ]
    }

  warranty_object = scrape(get_warranty_object)

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": None}

  print({
      "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": None})
  if equipment_scan_id and equipment_scan_id is not (None):
    r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                      "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": None}, timeout=30)
    print(r)

  if equipment_id and equipment_id is not (None):
    r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                      "warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": None}, timeout=30)
    print(r)
