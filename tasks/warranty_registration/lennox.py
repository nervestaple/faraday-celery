import time
from pathlib import Path
import urllib.parse

from celery_app import celery_app
from scrape import scrape


@celery_app.task
def register_lennox_warranty(payload):
  print(payload)

  def scraper(page):
    error = False
    download = None
    page.goto('https://www.warrantyyourway.com/')
    page.get_by_role('button", name="Dealer').click()
    page.get_by_label('Customer Number').click()
    page.get_by_label('Customer Number').fill(
      payload.get('lennox_company_code'))
    page.get_by_role('button", name="Continue').click()
    # page.pause()
    page.get_by_text('Existing Home').click()
    # page.pause()
    # page.get_by_text('Newly Constructed Home').click()
    # page.get_by_text('Commercial: Existing and New').click()
    # page.get_by_text('Existing Home').click()
    page.get_by_role('button", name="Next').click()
    # page.pause()
    # page.wait_for_load_state('domcontentloaded')
    # time.sleep(20)
    page.get_by_label('First Name').click()
    page.get_by_label('First Name').fill(payload.get('first_name'))
    # page.pause()
    page.get_by_label('Last Name').click()
    page.get_by_label('Last Name').fill(payload.get('last_name'))
    # page.pause()
    page.get_by_label('Please Enter Your Full').click()
    time.sleep(2)
    if payload.get('address').get('unit') != None and payload.get('address').get('unit') != None and payload.get('address').get('unit'):
      address_lookup = f"{payload.get('address').get('street')} {payload.get('address').get('unit')} {payload.get('address').get('city')} {payload.get('address').get('state')} {payload.get('address').get('zip')}"
      # unit =
    else:
      # address_lookup = f"{payload.get('address').get('street')}, {payload.get('address').get('city')} {payload.get('address').get('state')} {payload.get('address').get('zip')}"
      address_lookup = f"{payload.get('address').get('street')} {payload.get('address').get('city')} {payload.get('address').get('state')} {payload.get('address').get('zip')}"
    page.get_by_label('Please Enter Your Full').click()
    page.get_by_label('Please Enter Your Full').fill(address_lookup)
    # page.pause()
    try:
      time.sleep(2)
      page.locator('.pac-item-query').filter(
          has_text=f"{payload.get('address').get('street')}").first.click(timeout=1000)
      page.pause()
    except Exception as e:
      print('could not verify google address')
      try:
        page.get_by_label('Street address').click(force=True)
        page.get_by_label('Street address').fill(
            f"{payload.get('address').get('street')}")
        # page.pause()
        page.get_by_label('City').click()
        page.get_by_label('City').fill(f"{payload.get('address').get('city')}")
        # page.pause()
        page.get_by_label('Postal, Zip').fill(
            f"{payload.get('address').get('zip')}")
        page.get_by_label('Postal, Zip').click()
        page.get_by_label('State, Province').select_option(
          {payload.get('address').get('state')})
      except Exception as e:
        print('could not verify address')
        error = (
            f"could not verify google address: {payload.get('address').get('street')} {payload.get('address').get('unit')} {payload.get('address').get('city')} {payload.get('address').get('state')} {payload.get('address').get('zip')}")
    # page.pause()
    page.get_by_label('Phone').click()
    page.get_by_label('Phone').fill(payload.get('owner_phone') if payload.get(
      'owner_phone') != None else payload.get('installer_phone'))
    page.get_by_label('Owner Email').click()
    page.get_by_label('Owner Email').fill(payload.get('owner_email') if payload.get(
      'owner_email') != None else payload.get('installer_email'))
    # page.pause()
    page.get_by_label('Dealer Email').click()
    # page.pause()
    page.get_by_label('Dealer Email').press('ControlOrMeta+a')
    # page.pause()
    page.get_by_label('Dealer Email').fill(payload.get('installer_email'))

    # page.get_by_label('Equipment Eligibility').locator('div').filter(has_text="Equipment Eligibility').nth(1).click()
    # page.get_by_text('Close').click()
    # page.get_by_text('I have reviewed the').click()
    # page.get_by_label('Equipment Eligibility').get_by_label('Close').click()
    # page.get_by_text('I have reviewed the').click()
    # page.get_by_text('Close').click()
    # page.get_by_text('I have reviewed the').click()
    # page.get_by_label('Equipment Eligibility').get_by_label('Close').click()
    # page.pause()
    page.locator('#agree').click(force=True)
    # page.pause()
    # page.get_by_label('Equipment Eligibility').get_by_label('Close').click()
    # page.pause()
    time.sleep(5)
    page.get_by_role('button", name="Next').click(timeout=5000)
    try:
      page.get_by_text('Please provide a street').click(timeout=2000)
      page.get_by_label('Street address').click(force=True)
      page.get_by_label('Street address').fill(
          f"{payload.get('address').get('street')}")
      # page.pause()
      page.get_by_label('City').click()
      page.get_by_label('City').fill(f"{payload.get('address').get('city')}")
      # page.pause()
      page.get_by_label('Postal, Zip').fill(
          f"{payload.get('address').get('zip')}")
      page.get_by_label('Postal, Zip').click()
      page.get_by_label('State, Province').select_option(
        {payload.get('address').get('state')})
    except Exception as e:
      print('address entered')
    # page.pause()
    try:
      # page.pause()
      page.get_by_text('Suggested Address(es)').click(timeout=5000)
      suggested_address = page.locator(
        '#suggested-address-list').click(timeout=5000)
      # page.pause()
      # suggested_address.get_by_role('input').click()
      # page.pause()
      page.get_by_role('button", name="Continue').click(force=True)

    except Exception as e:
      print(f"something bad happened: {e}")
    finally:
      systems = payload.get('equipment')
      for system in systems:
        equipments = system.get('equipment')
        page.get_by_text('Tell Us About The Equipment').click(timeout=2000)
        # time.sleep(20)
        for equipment in equipments:
          # page.pause()
          page.get_by_label('Serial Number', exact=True).click(timeout=2000)
          page.get_by_label('Serial Number', exact=True).fill(
            equipment.get('serial_number'))
          # page.pause()
          page.get_by_placeholder('mm/dd/yyyy').click(timeout=2000)
          time.sleep(2)
          # page.pause()
          page.get_by_placeholder(
            'mm / dd / yyyy').fill(payload.get('install_date'))
          time.sleep(2)
          page.get_by_placeholder('mm/dd/yyyy').press('Enter')
          # page.get_by_role('heading", name="Tell Us About The Equipment').click()
          # page.pause()
          # try:
          #   page.locator('#addSerialButton').click(force=True)
          # except Exception as e:
          #   print(e)
          #   return e
          # page.pause()
          #
          # time.sleep(2)
          # page.get_by_role('button", name="Add').click(force=True)
          # xpage.pause()

          # check to see if serial number is registered
          print('checking to see if serial number is already registered')
          try:
            page.get_by_text(
              'This serial number is previously registered and cannot be registered again').click(timeout=2000)
            error = (
              f"Serial number previously registered: {equipment.get('serial_number')}")
            print(
              f"Serial number previously registered: {equipment.get('serial_number')}")
            return error
          except Exception as e:
            print('serial number not registered')

          # check to see if non serialized item
          print('checking to see if non serialized item')
          try:
            page.locator('#nonSerialInputForm').click(timeout=2000)
            page.pause()
            if equipment.get('warranty_model') != None and equipment.get('warranty_model') != None:
              warranty_model = equipment.get('warranty_model')
              # page.pause()
              optionToSelect = page.locator(
                'option', has_text=f'{warranty_model}').text_content()
              print(optionToSelect)
              page.get_by_label('Product Type').select_option(optionToSelect)
              # page.pause()
              page.get_by_label('Brand').select_option('Lennox')
              page.get_by_placeholder('Enter Model').click()
              page.get_by_placeholder('Enter Model').fill(f"{warranty_model}")
              page.locator('#addNonSerialAddButton').click()
            # Heat Strips
            elif equipment.get('type_id') == 115:
              warranty_model = None
              for parent_equipment in equipments:
                if parent_equipment.get('warranty_model') != None and parent_equipment.get('warranty_model') != None:
                  warranty_model = parent_equipment.get('warranty_model')
                  optionToSelect = page.locator(
                    'option', has_text=f'{warranty_model}').text_content()
                  print(optionToSelect)
                  page.get_by_label(
                    "Product Type").select_option(optionToSelect)
                  # page.pause()
                  page.get_by_label('Brand').select_option('Lennox')
                  page.get_by_placeholder('Enter Model').click()
                  page.get_by_placeholder('Enter Model').fill(
                    f"{equipment.get('model')}")
                  page.locator('#addNonSerialAddButton').click()
                  break
                else:
                  continue
              if warranty_model:
                print('found heat strip model')
              else:
                print(f"no warranty model for: {equipment.get('model')}")
                error = f"no warranty model for: {equipment.get('model')}"
                return error
            # Dampers
            elif equipment.get('type_id') == 50 or equipment.get('type_id') == 181 or equipment.get('type_id') == 8:
              optionToSelect = page.locator(
                'option', has_text="Dampers").first.text_content()
              print(optionToSelect)
              page.get_by_label('Product Type').select_option(optionToSelect)
              # page.pause()
              page.get_by_label('Brand').select_option('Lennox')
              page.get_by_placeholder('Enter Model').click()
              page.get_by_placeholder('Enter Model').fill(
                f"{equipment.get('model')}")
              page.locator('#addNonSerialAddButton').click()
            else:
              print(f"no warranty model for: {equipment.get('model')}")
              error = f"no warranty model for: {equipment.get('model')}"
              return error
          except Exception as e:
            print(f"something bad happened: {e}")

          # check to see if serial number was submitted correctly
          print('checking to see if serial number was submitted correctly')
          try:
            # page.pause()
            time.sleep(2)
            equipment_rows = page.locator(
              '.equipment-rows').click(timeout=2000)
            equipment_rows = page.locator('.equipment-rows')
            print(equipment_rows)
            # page.pause()
            equipment_rows.get_by_text(equipment.get(
              'serial_number')).click(timeout=2000)
            serial = equipment_rows.get_by_text(equipment.get('serial_number'))
            print(serial.text_content())
          except Exception as e:
            print(f"something bad happened: {e}")
            print(
              f"Could not find serial number: {equipment.get('serial_number')}")
            error = f"Could not find serial number: {equipment.get('serial_number')}"
            return error
      page.get_by_role('button", name="Next').click()
      # Check to see if lennox warranty is down
      # page.pause()
      # Section to select coil matches
      print('Looking for coil pairings')
      try:
        page.locator('.ac-group-title').click(timeout=2000)
        systems = payload.get('equipment')
        coil_number = 0
        for system in systems:
          page.locator('.row-container').locator(f'nth={coil_number}').click()
          coil_pairing = page.locator(
            '.row-container').locator(f'nth={coil_number}')
          print(coil_pairing)
          equipments = system.get('equipment')
          for equipment in equipments:
            try:
              # page.pause()
              coil_pairing.locator('span').filter(
                has_text=f"{equipment.get('serial_number')}").click(timeout=2000)
              coil_pairing.locator('select').click(timeout=2000)
              # coil_pairing=page.get_by_text(f'{equipment.get('serial_number')}').click(timeout=2000)
              # coil_pairing.locator(f'#{equipment.get('serial_number')}').click(timeout=2000)
              for coil in equipments:
                try:
                  # page.pause()
                  option_to_select = coil_pairing.locator('option').filter(
                    has_text=f"{coil.get('serial_number')}").first.text_content()
                  coil_pairing.locator(
                    'select').select_option(option_to_select)
                  # page.locator('option').filter(has_text=f"{coil.get('serial_number')}').first.click(timeout=5000)
                  break
                except Exception as e:
                  print(
                    f"could not find coil pairing: {coil.get('serial_number')}")
            except Exception as e:
              print(
                f"could not find AC Unit pairing: {equipment.get('serial_number')}")
          coil_number += 1
        page.get_by_role('button", name="Next').click(timeout=2000)

      except Exception as e:
        print('no coil pairings')

      # <select class="pairing-coil form-control" onfocus="onCoilSelectFocus(this)" onchange="onCoilSelect(this)" id="5824H01302" required=""> <option selected="" value="" class="option-background">Select pairing coil</option><option value="skip-pairing" class="option-background">Skip pairing</option><option value="1524H04108-2024-09-10" class="OneLinkNoTx option-background ">1524H04108 - CK40CT-60C Coil 5.0 Ton R410A/R454B - 09/09/2024</option><option value="1524H04106-2024-09-10" class="OneLinkNoTx option-background ">1524H04106 - CK40CT-60C Coil 5.0 Ton R410A/R454B - 09/09/2024</option></select>

      # #ac-group-title
      # .equipment-rows
      # page.pause()
      try:
        page.get_by_role(
          "heading", name="Warranty Your Way is ").click(timeout=5000)
        error = "Lennox site is NOT working"
        print('Lennox site is NOT working')
        return error
      except Exception as e:
        print('Lennox site is working')

      # Section to select coil matches
      try:
        page.get_by_role('button", name="Next').click()
      # page.pause()
      except Exception as e:
        print(f"something bad happened: {e}")

      select_all_warranties = False
      while select_all_warranties == False:
        try:
          page.get_by_text('$000.00').click(timeout=2000)
          page.get_by_role('button", name="Select').click()
        except Exception as e:
          try:
            page.get_by_role('button", name="Select').click(timeout=2000)

          except Exception as e:
            print(f"something bad happened: {e}")
            print(f"something bad happened: {e}")
            break
      all_equipment_reviewed = False
      while all_equipment_reviewed == False:
        try:
          page.get_by_role('button", name="Review Next').click(timeout=2000)
        except Exception as e:
          print('all equipment has been reviewed')
          break

      try:
        page.get_by_role(
          "heading", name="Warranty Your Way is ").click(timeout=5000)
        error = "Lennox site is NOT working"
        print('Lennox site is NOT working')
        return error
      except Exception as e:
        print('Lennox site is working')
      # page.pause()
      try:
        page.locator('#lii-terms').click(force=True)
        page.locator('#lii-terms').click(force=True)
        page.locator('#lii-terms').click(force=True)
        # page.pause()
      except Exception as e:
        print("couldn't click terms")
      page.pause()
      page.get_by_role('button", name="Submit & Checkout').click()
      # page.pause()
      page.get_by_text('Submit & Checkout Please').click()
      # page.pause()
      page.get_by_label('Submit & Checkout Please').get_by_role(
        "button", name="Submit & Checkout").click(force=True)
      time.sleep(5)
      with page.expect_download() as download_info:
        page.get_by_role('link", name="View/Download Registration').click()
      download = download_info.value
      file_name = urllib.parse.quote(
        f"lennox_warranty_{payload.get('first_name')}_{payload.get('last_name')}_{payload.get('st_job_id')}.pdf").lower()
      print(file_name)
      print('saving download')
      download.save_as(Path.home().joinpath('Downloads', file_name))

      # download.save_as(download.suggested_filename)

    # ---------------------

  scrape(scraper)
