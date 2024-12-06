from collections import defaultdict
from dotenv import load_dotenv
import requests
import time

from celery_app import celery_app
from manufacturers import manufacturers, parent_manufacturers, manufacturer_name_by_id
from tasks.warranty_registration.carrier import register_carrier_warranty
from tasks.warranty_registration.daikin import register_daikin_warranty
from tasks.warranty_registration.lennox import register_lennox_warranty
from tasks.warranty_registration.trane import register_trane_warranty

load_dotenv()

warranty_registration_methods = {
  # manufacturers['Carrier']: register_carrier_warranty,
  manufacturers['Lennox']: register_lennox_warranty,
  manufacturers['Trane']: register_trane_warranty,
  manufacturers['Daikin']: register_daikin_warranty,
  manufacturers['Goodman']: register_daikin_warranty
}


def register_warranties(payload):
  job_id = payload['job_id']
  name_tokens = payload['name'].split(' ')
  payload['first_name'] = ' '.join(name_tokens[0:-1])
  payload['last_name'] = name_tokens[-1]

  print('Warranty registration payload:', payload)

  filtered_equipment = filter_equipment_by_install_date(payload)
  systems_by_manufacturer = group_equipment_by_manufacturer_and_system(
    filtered_equipment)
  print('Systems by manufacturer:', systems_by_manufacturer)

  for manufacturer_id, systems_by_name in systems_by_manufacturer.items():
    register_method = warranty_registration_methods.get(manufacturer_id)
    if not register_method:
      continue

    systems = list(systems_by_name.values())
    print(
      f'Registering warranties for job_id: {job_id}, manufacturer_id: {manufacturer_id}')
    print('Systems:', systems)
    register_warranty_for_manufacturer.delay(manufacturer_id, payload, systems)


@celery_app.task
def register_warranty_for_manufacturer(manufacturer_id, payload, systems):
  job_id = payload['job_id']
  print(
    f'Starting warranty registration task for manufacturer_id: {manufacturer_id}, job_id: {job_id}')
  register_method = warranty_registration_methods.get(manufacturer_id)
  if not register_method:
    print(
      f'Missing warranty registration method for manufacturer_id: {manufacturer_id}, job_id: {job_id}, quitting...')
    return

  warranty_s3_url, error_reason = register_method(payload, systems)

  post_body = {
    'warranty': warranty_s3_url,
    'st_jobs_id': payload['job_id'],
    'companies_id': payload['companies_id'],
    'manufacturer': manufacturer_name_by_id[manufacturer_id],
    'needs_review': error_reason is not None,
    'warranty_review_reason': error_reason,
    'approved': False
  }

  print('registering warranty and posting to xano:', post_body)
  TRIES = 3
  for try_num in range(TRIES):
    try:
      r = requests.post(
        'https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/warranty_upload', data=post_body, timeout=120)
      print(r)
      break
    except Exception as e:
      if try_num == TRIES - 1:
        print(f'failed posting to xano after {TRIES} tries, giving up')
        return
      print(e)
      print('failed posting to xano, trying again...')
      time.sleep(5)


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
