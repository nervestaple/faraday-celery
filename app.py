import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response
from tasks import identify_new_model, getCarrierWarranty, getTraneWarranty, getYorkWarranty, getLennoxWarranty, get_rheem_warranty, manual_lookup, test_task, sum_test_task, get_bradford_white_warranty
from bs4 import BeautifulSoup
import redis
import json

from manufacturers import manufacturers

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')


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

  # Carrier Warranty Lookup
  if manufacturer_id == manufacturers['Carrier']:
    if int(instant) == 1:
      warranty_data = getCarrierWarranty(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return jsonify(warranty_data)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getCarrierWarranty.delay(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)

  # Trane Warranty Lookup
  elif manufacturer_id == manufacturers['Trane']:
    if int(instant) == 1:
      warranty_data = getTraneWarranty(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return jsonify(warranty_data)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getTraneWarranty.delay(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)

  # York Warranty Lookup
  elif manufacturer_id == manufacturers['York']:
    if int(instant) == 1:
      warranty_data = getYorkWarranty(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return jsonify(warranty_data)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getYorkWarranty.delay(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)

  # Lennox Warranty Lookup
  elif manufacturer_id == manufacturers['Lennox']:
    if int(instant) == 1:
      warranty_data = getLennoxWarranty(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return jsonify(warranty_data)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getLennoxWarranty.delay(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)

  elif manufacturer_id == manufacturers['Rheem']:
    if int(instant) == 1:
      warranty_data = get_rheem_warranty(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return jsonify(warranty_data)
      else:
        return Response(None, status=500)
    else:
      warranty_data = get_rheem_warranty.delay(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)

  elif manufacturer_id == manufacturers['Bradford White']:
    if int(instant) == 1:
      warranty_data = get_bradford_white_warranty(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return jsonify(warranty_data)
      else:
        return Response(None, status=500)
    else:
      warranty_data = get_bradford_white_warranty.delay(
          serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)


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

  redis_client.set('lennoxAuthCode', code)
  return Response('Code saved', status=200)
