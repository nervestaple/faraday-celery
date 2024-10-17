from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
import os
from api.tasks import identify_new_model, getCarrierWarranty, getTraneWarranty, getYorkWarranty, getLennoxWarranty, manual_lookup
from PIL import Image
from io import BytesIO
import requests
from rest_framework.response import Response


# Create your views here.
def index(request):
    return render(request, 'index.html')

class AddNewModel(APIView):

  def post(self, request, *args, **kwargs):
    data = {
      'model_number': request.data.get('model_number'),
      'supporting_data': request.data.get('supporting_data'),
      'instant': request.data.get('instant')
          }
    model_number = data['model_number']
    supporting_data = data['supporting_data']
    instant = data['instant']
    if instant:
      #return Response("hey", status=status.HTTP_200_OK)
      model = identify_new_model(model_number, supporting_data)
      return Response(model, status=status.HTTP_200_OK)
    else:
      model = identify_new_model.delay(model_number, supporting_data)
      return Response(model_number, status=status.HTTP_200_OK)

class ManualLookup(APIView):

  def post(self, request, *args, **kwargs):
    data = {
      'model_number': request.data.get('model_number'),
      'manufacturer': request.data.get('manufacturer'),
      'equipment_type': request.data.get('equipment_type'),
      'model_id': request.data.get('model_id')
          }
    model_number = data['model_number']
    manufacturer = data['manufacturer']
    equipment_type = data['equipment_type']
    model_id = data['model_id']
    manual = manual_lookup.delay(model_number, manufacturer, equipment_type, model_id)
    try:
      return Response(model_id, status=status.HTTP_200_OK)
    except Exception as e:
      print(f"something went wrong {e}")
    finally:
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', json={"warranty_object": warranty_object, "equipment_scan_id": equipment_scan_id}, timeout=30)


class WarrantyLookup(APIView):

  def post(self, request, *args, **kwargs):
    data = {
      'manufacturer': request.data.get('manufacturer'),
      'last_name': request.data.get('last_name'),
      'serial_number': request.data.get('serial_number'),
      'instant': request.data.get('instant'),
      'equipment_scan_id': request.data.get('equipment_scan_id'),
      'equipment_id': request.data.get('equipment_id')
          }
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
          return Response(warranty_data, status=status.HTTP_200_OK)
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
          return Response(warranty_data, status=status.HTTP_200_OK)
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
          return Response(warranty_data, status=status.HTTP_200_OK)
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
          return Response(warranty_data, status=status.HTTP_200_OK)
        else:
          return Response(None, status=500)
      else:
        warranty_data = getLennoxWarranty.delay(serial_number, instant, equipment_scan_id, equipment_id, last_name)
        return Response(serial_number, status=200)