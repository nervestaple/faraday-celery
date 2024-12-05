import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response
from bs4 import BeautifulSoup
import redis
import json

from constants import LENNOX_AUTH_CODE_KEY
from tasks import sum_test_task, test_task
from tasks.warranty_lookup import warranty_lookups_by_manufacturer_id
from tasks.identify_new_model import identify_new_model
from tasks.warranty_registration import register_warranties

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')


@app.after_request
def after_request(response):
  if response.status_code == 499:
    try:
      print('CLIENT CLOSED: 499, printing request.json', request.json)
    except Exception as e:
      pass
  return response


@app.route('/hello', methods=['GET'])
def index():
  return 'Hello, Faraday!'


@app.route('/test', methods=['GET'])
def test():
  test_task.delay()
  return 'started...'


@app.route('/test-add', methods=['GET'])
def test_add():
  a = int(request.args.get('a'))
  b = int(request.args.get('b'))
  sum_test_task.delay(a, b)
  return 'started...'


@app.route('/model', methods=['POST'])
def add_new_model():
  data = request.json
  model_number = data['model_number']
  supporting_data = data['supporting_data']
  instant = data['instant']
  if instant:
    # return Response("hey", status=status.HTTP_200_OK)
    model = identify_new_model(model_number, supporting_data)
    return jsonify(model)
  else:
    identify_new_model.delay(model_number, supporting_data)
    return Response(model_number, status=200)


@app.route('/manual-lookup', methods=['POST'])
def manual_lookup():
  data = request.json
  model_number = data['model_number']
  manufacturer = data['manufacturer']
  equipment_type = data['equipment_type']
  model_id = data['model_id']
  manual_lookup.delay(model_number, manufacturer, equipment_type, model_id)
  try:
    return Response(model_id, status=200)
  except Exception as e:
    print(f"something went wrong {e}")
  finally:
    # requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', json={"warranty_object": warranty_object, "equipment_scan_id": equipment_scan_id}, timeout=30)
    pass


@app.route('/warranty', methods=['POST'])
def warranty_lookup():
  print('warranty lookup', request.json)
  data = request.json
  manufacturer = data['manufacturer']
  last_name = data['last_name']
  serial_number = data['serial_number']
  instant = data['instant']
  equipment_scan_id = data['equipment_scan_id']
  equipment_id = data['equipment_id']

  manufacturer_id = int(manufacturer)
  if manufacturer_id not in warranty_lookups_by_manufacturer_id:
    return Response('Manufacturer not supported', status=400)

  lookup = warranty_lookups_by_manufacturer_id[manufacturer_id]

  if int(instant) == 1:
    warranty_data = lookup(
        serial_number, instant, equipment_scan_id, equipment_id, last_name)
    if warranty_data:
      return jsonify(warranty_data)
    else:
      return Response(None, status=500)
  else:
    warranty_data = lookup.delay(
        serial_number, instant, equipment_scan_id, equipment_id, last_name)
    return Response(serial_number, status=200)


@app.route('/warranty-registration', methods=['POST'])
def warranty_registration():
  payload = request.json
  register_warranties(payload)
  return Response('Registering warranties...', status=200)


redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL'), db=0)


@app.route('/lennox-auth-code', methods=['POST'])
def lennox_auth_code():
  data = request.json
  print(json.dumps(data))
  html = data.get('html')
  if not html:
    return Response('Missing html', status=400)

  soup = BeautifulSoup(html, 'html.parser')
  cells = soup.select('tbody > tr > td')
  if len(cells) == 0:
    return Response('Could not find code', status=400)

  code = cells[-1].get_text()
  if not code:
    return Response('Could not find code', status=400)

  redis_client.set(LENNOX_AUTH_CODE_KEY, code)
  return Response('Code saved', status=200)
