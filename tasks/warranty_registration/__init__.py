from collections import defaultdict
from dotenv import load_dotenv
import requests

from celery_app import celery_app
from manufacturers import manufacturers, parent_manufacturers, manufacturer_name_by_id
from tasks.warranty_registration.carrier import register_carrier_warranty
from tasks.warranty_registration.daikin import register_daikin_warranty
from tasks.warranty_registration.lennox import register_lennox_warranty
from tasks.warranty_registration.trane import register_trane_warranty

load_dotenv()

# payload = {
#   "name": "Hershall Kaufman",
#   "first_name": "Hershall",
#   "last_name": "Kaufman",
#   "address": {
#     "zip": "85718",
#     "city": "Tucson",
#     "unit": "",
#     "state": "AZ",
#     "street": "5111 North Soledad Primera",
#     "country": "USA",
#     "latitude": 32.3003611,
#     "longitude": -110.9503376
#   },
#   "type": "Residential",
#   "owner_email": "kaufmanhw@yahoo.com",
#   "owner_phone": "5202351355",
#   "install_date": "09/21/2024",
#   "installer_name": "Rite Way Heating, Cooling & Plumbing",
#   "installer_email": "Althaea.balda@ritewayac.com",
#   "installer_phone": "520-745-0660",
#   "lennox_company_code": "C14882",
#   "equipment": [
#     {
#       "id": 1022330,
#       "manufacturer": "Trane",
#       "model": "4TTR6048N1000AA",
#       "serial_number": "23454WL8HF",
#       "installed_on": "09/21/2024",
#       "image": "https://x6fl-8ass-7cr7.n7.xano.io/vault/DutTGvHh/8_Puvao-vLhPfoqqW6UXHkF9bsE/s9IFQQ../f9b2c8a0-fa16-4778-9bae-a4cf97594ed7_cdv_photo_001-l7byzy1ydnj.jpg",
#       "system_name": null,
#       "manufacturer_id": 1,
#       "type_id": 1,
#       "warranty_model": null
#     },
#     {
#       "id": 1022331,
#       "manufacturer": "Trane",
#       "model": "4TXCC007D83HCBA",
#       "serial_number": "24326P25BG",
#       "installed_on": "09/21/2024",
#       "image": "https://x6fl-8ass-7cr7.n7.xano.io/vault/DutTGvHh/aj20mErlvI_e1wDc4v7qaEU-7OQ/sdpD9w../f9b2c8a0-fa16-4778-9bae-a4cf97594ed7_cdv_photo_001-l7byzy1ydnj.jpg",
#       "system_name": null,
#       "manufacturer_id": 1,
#       "type_id": 16,
#       "warranty_model": null
#     },
#     {
#       "id": 1022332,
#       "manufacturer": "Trane",
#       "model": "TCONT824AS52DC",
#       "serial_number": "2410DFB93X",
#       "installed_on": "09/21/2024",
#       "image": "https://x6fl-8ass-7cr7.n7.xano.io/vault/DutTGvHh/OuOMX0j1JJRvqurr3MpOY7cwQL0/TZ0s9w../f9b2c8a0-fa16-4778-9bae-a4cf97594ed7_cdv_photo_001-l7byzy1ydnj.jpg",
#       "system_name": null,
#       "manufacturer_id": 1,
#       "type_id": 8,
#       "warranty_model": null
#     }
#   ],
#   "st_job_id": 320089143,
#   "job_id": 1781848,
#   "companies_id": 34
# }

warranty_registration_methods = {
  # manufacturers['Carrier']: register_carrier_warranty,
  manufacturers['Lennox']: register_lennox_warranty,
  manufacturers['Trane']: register_trane_warranty,
  manufacturers['Daikin']: register_daikin_warranty,
  manufacturers['Goodman']: register_daikin_warranty
}


def register_warranties(payload):
  name_tokens = payload['name'].split(' ')
  payload['first_name'] = ' '.join(name_tokens[0:-1])
  payload['last_name'] = name_tokens[-1]

  filtered_equipment = filter_equipment_by_install_date(payload)
  systems_by_manufacturer = group_equipment_by_manufacturer_and_system(
    filtered_equipment)
  print('Systems by manufacturer:', systems_by_manufacturer)

  for manufacturer_id, systems_by_name in systems_by_manufacturer.items():
    register_method = warranty_registration_methods.get(manufacturer_id)
    if not register_method:
      continue

    systems = list(systems_by_name.values())
    print('Registering warranties for manufacturer:', manufacturer_id)
    print('Systems:', systems)
    register_warranty_for_manufacturer.delay(manufacturer_id, payload, systems)


@celery_app.task
def register_warranty_for_manufacturer(manufacturer_id, payload, systems):
  register_method = warranty_registration_methods.get(manufacturer_id)
  if not register_method:
    return

  warranty_s3_url, error_reason = register_method(payload, systems)

  post_body = {
    'warranty': warranty_s3_url,
    'st_jobs_id': payload['job_id'],
    'companies_id': payload['companies_id'],
    'manufacturer': manufacturer_name_by_id[manufacturer_id],
    'needs_review': error_reason is not None,
    'warranty_review_reason': error_reason
  }
  r = requests.post(
    'https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/warranty_upload', data=post_body, timeout=30)
  print(r)


def filter_equipment_by_install_date(payload):
  install_date = payload['install_date']
  filtered_equipment = [equipment for equipment in payload['equipment']
                        if equipment['installed_on'] == install_date]
  return filtered_equipment


def group_equipment_by_manufacturer_and_system(equipment):
  systems_by_manufacturer = defaultdict(lambda: defaultdict(list))

  for equipment_item in equipment:
    manufacturer_id = equipment_item['manufacturer_id']

    if manufacturer_id in parent_manufacturers:
      manufacturer_id = parent_manufacturers[manufacturer_id]

    system_name = equipment_item['system_name'] or ''
    systems_by_manufacturer[manufacturer_id][system_name].append(
      equipment_item)

  return systems_by_manufacturer
