import re
import requests

from dotenv import load_dotenv

from celery_app import celery_app
from s3 import upload_remote_warranty_pdf_to_s3

load_dotenv()


RHEEM_CLIENT_ID = '7754f947-044b-4c2a-8613-790e3e255b00.apps.rheemapi.com'
rheem_headers = {
  "accept": "application/json, text/javascript, */*; q=0.01",
  "accept-language": "en-US,en;q=0.9",
  "content-type": "application/json; charset=utf-8",
  "priority": "u=1, i",
  "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": "\"macOS\"",
  "sec-fetch-dest": "empty",
  "sec-fetch-mode": "cors",
  "sec-fetch-site": "cross-site",
  "x-requested-with": "XMLHttpRequest",
  "Referer": "https://rheem.registermyunit.com/",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "x-clientid": RHEEM_CLIENT_ID,
}

RHEEM_SERIAL_REGEX = r'^(RHLN|RULN|RHNG|RMLN|RHUN|RUNG|RUUN|LWLP|GENG|RULP|ESLP|RHLP|RLP|GELN|GELP|RMNG|RMLP|GELW|GEUN|RNG|RCN|RUN|VGN|RN|RU|RO|RH|RM|SN|GE|RC|R)'


@celery_app.task
def get_rheem_warranty(serial_number_raw, instant, equipment_scan_id, equipment_id, owner_last_name):
  serial_number = re.sub(RHEEM_SERIAL_REGEX, '', serial_number_raw).strip()
  print(serial_number)
  bearer_token = get_rheem_bearer_token()
  response = requests.get(
    f"https://resource.myrheem.com/v1/rmu/verify?SerialNumber={serial_number}&HomeownerLastName={owner_last_name}",
    headers={
      "authorization": f"Bearer {bearer_token}",
      **rheem_headers
    }
  )
  response = response.json()
  print('rheem response:', response)
  if response is None or 'WarrantyDetails' not in response:
    print("rheem response is missing or malformed")
    return None

  is_registered = 'RegistrationDate' in response and len(
    response['RegistrationDate']) > 5

  warranties = [{
    "name": w['WarrantyItem'],
    "description": w['WarrantyItem'],
    "start_date": w['WarrantyStartDate'],
    "end_date": w['WarrantyEndDate'],
    "type": w['WarrantyType']
  } for w in response['WarrantyDetails']]

  certificate = None
  if response['CertificateURL']:
    certificate = upload_remote_warranty_pdf_to_s3(
      response['CertificateURL'], {'manufacturer_name': 'rheem'})

  return {
    "model_number": response['ModelNumber'],
    "install_date": response['InstallationDate'],
    "is_registered": is_registered,
    "register_date": response['RegistrationDate'] if is_registered else None,
    "last_name_match": is_registered,
    "shipped_date": response['ShipDate'],
    "warranties": warranties,
    "certificate": certificate,
  }


def get_rheem_bearer_token():
  response = requests.get(
    f"https://auth.myrheem.com/v1/oauth2/authorize?response_type=token&client_id={RHEEM_CLIENT_ID}",
    headers={**rheem_headers}
  )

  response = response.json()
  bearer_token = response['access_token']
  return bearer_token
