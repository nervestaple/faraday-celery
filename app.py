import os
from flask import Flask, render_template, request, Response
from tasks import identify_new_model, getCarrierWarranty, getTraneWarranty, getYorkWarranty, getLennoxWarranty, manual_lookup, test_task, sum_test_task
import requests

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
    #return Response("hey", status=status.HTTP_200_OK)
    model = identify_new_model(model_number, supporting_data)
    return Response(model, status=200)
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
  data = request.json
  manufacturer = data['manufacturer']
  last_name = data['last_name']
  serial_number = data['serial_number']
  instant = data['instant']
  equipment_scan_id = data['equipment_scan_id']
  equipment_id = data['equipment_id']
  
  ## Carrier Warranty Lookup
  if int(manufacturer) == 2:
    if int(instant) == 1:
      warranty_data = getCarrierWarranty(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return Response(warranty_data, status=200)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getCarrierWarranty.delay(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)
  
  ## Trane Warranty Lookup     
  elif int(manufacturer) == 1:
    if int(instant) == 1:
      warranty_data = getTraneWarranty(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return Response(warranty_data, status=200)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getTraneWarranty.delay(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)
  
  ## York Warranty Lookup     
  elif int(manufacturer) == 25:
    if int(instant) == 1:
      warranty_data = getYorkWarranty(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return Response(warranty_data, status=200)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getYorkWarranty.delay(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)

  ## Lennox Warranty Lookup     
  elif int(manufacturer) == 22:
    if int(instant) == 1:
      warranty_data = getLennoxWarranty(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      if warranty_data:
        return Response(warranty_data, status=200)
      else:
        return Response(None, status=500)
    else:
      warranty_data = getLennoxWarranty.delay(serial_number, instant, equipment_scan_id, equipment_id, last_name)
      return Response(serial_number, status=200)