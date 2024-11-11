import dotenv
import dotenv
import time
from pathlib import Path
from itertools import groupby
from operator import itemgetter
from pathlib import Path
import urllib.parse
from collections import defaultdict

null = None
false = False
true = True

dotenv.load_dotenv()

payload = {
  "name": "Hershall Kaufman",
  "first_name": "Hershall",
  "last_name": "Kaufman",
  "address": {
    "zip": "85718",
    "city": "Tucson",
    "unit": "",
    "state": "AZ",
    "street": "5111 North Soledad Primera",
    "country": "USA",
    "latitude": 32.3003611,
    "longitude": -110.9503376
  },
  "type": "Residential",
  "owner_email": "kaufmanhw@yahoo.com",
  "owner_phone": "5202351355",
  "install_date": "09/21/2024",
  "installer_name": "Rite Way Heating, Cooling & Plumbing",
  "installer_email": "Althaea.balda@ritewayac.com",
  "installer_phone": "520-745-0660",
  "lennox_company_code": "C14882",
  "equipment": [
    {
      "id": 1022330,
      "manufacturer": "Trane",
      "model": "4TTR6048N1000AA",
      "serial_number": "23454WL8HF",
      "installed_on": "09/21/2024",
      "image": "https://x6fl-8ass-7cr7.n7.xano.io/vault/DutTGvHh/8_Puvao-vLhPfoqqW6UXHkF9bsE/s9IFQQ../f9b2c8a0-fa16-4778-9bae-a4cf97594ed7_cdv_photo_001-l7byzy1ydnj.jpg",
      "system_name": null,
      "manufacturer_id": 1,
      "type_id": 1,
      "warranty_model": null
    },
    {
      "id": 1022331,
      "manufacturer": "Trane",
      "model": "4TXCC007D83HCBA",
      "serial_number": "24326P25BG",
      "installed_on": "09/21/2024",
      "image": "https://x6fl-8ass-7cr7.n7.xano.io/vault/DutTGvHh/aj20mErlvI_e1wDc4v7qaEU-7OQ/sdpD9w../f9b2c8a0-fa16-4778-9bae-a4cf97594ed7_cdv_photo_001-l7byzy1ydnj.jpg",
      "system_name": null,
      "manufacturer_id": 1,
      "type_id": 16,
      "warranty_model": null
    },
    {
      "id": 1022332,
      "manufacturer": "Trane",
      "model": "TCONT824AS52DC",
      "serial_number": "2410DFB93X",
      "installed_on": "09/21/2024",
      "image": "https://x6fl-8ass-7cr7.n7.xano.io/vault/DutTGvHh/OuOMX0j1JJRvqurr3MpOY7cwQL0/TZ0s9w../f9b2c8a0-fa16-4778-9bae-a4cf97594ed7_cdv_photo_001-l7byzy1ydnj.jpg",
      "system_name": null,
      "manufacturer_id": 1,
      "type_id": 8,
      "warranty_model": null
    }
  ],
  "st_job_id": 320089143,
  "job_id": 1781848,
  "companies_id": 34
}


def group_equipment_by_manufacturer(data):
  equipment = data['equipment']

  # Sort the equipment by manufacturer_id to prepare for grouping
  equipment.sort(key=itemgetter('manufacturer_id'))

  # Group the equipment by manufacturer_id
  grouped_equipment = []
  for manufacturer_id, group in groupby(equipment, key=itemgetter('manufacturer_id')):
    grouped_equipment.append({
        'manufacturer_id': manufacturer_id,
        'equipment': list(group)
    })

  return grouped_equipment

# Function to filter equipment based on install date


def filter_equipment_by_install_date(data):
  install_date = data['install_date']
  filtered_equipment = [equipment for equipment in data['equipment']
                        if equipment['installed_on'] == install_date]
  data['equipment'] = filtered_equipment
  return data

# Function to get equipment by manufacturer_id


def get_equipment_by_manufacturer_id(grouped_equipment, manufacturer_ids):
  # List to store the equipment matching the provided manufacturer_ids
  matched_equipment = []

  # Loop through each group and check if its manufacturer_id is in the provided list
  for group in grouped_equipment:
    if group['manufacturer_id'] in manufacturer_ids:
      # Add matching equipment to the result list
      matched_equipment.extend(group['systems'])

  return matched_equipment

# Function to group by manufacturer_id and then system_name


def group_equipment_by_manufacturer_and_system(data):
  equipment_by_manufacturer = defaultdict(lambda: defaultdict(list))

  # Iterate over the equipment
  for equipment in data['equipment']:
    manufacturer_id = equipment['manufacturer_id']
    system_name = equipment['system_name']

    # Group by manufacturer_id and system_name if system_name is not blank or null
    if system_name:
      equipment_by_manufacturer[manufacturer_id][system_name].append(equipment)
    else:
      equipment_by_manufacturer[manufacturer_id][null].append(equipment)

  # Transform the grouped data into the desired structure
  grouped_result = []
  for manufacturer_id, systems in equipment_by_manufacturer.items():
    systems_list = []
    for system_name, equipment_list in systems.items():
      systems_list.append({
          'system_name': system_name,
          'equipment': equipment_list
      })
    grouped_result.append({
        'manufacturer_id': manufacturer_id,
        'systems': systems_list
    })

  # Return the final structure
  return grouped_result


# Lennox
def registerLennox(payload):
  print(payload)

  from playwright.sync_api import Playwright, sync_playwright

  def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    # browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    error = False
    download = None
    page.goto("https://www.warrantyyourway.com/")
    page.get_by_role("button", name="Dealer").click()
    page.get_by_label("Customer Number").click()
    page.get_by_label("Customer Number").fill(
      payload.get('lennox_company_code'))
    page.get_by_role("button", name="Continue").click()
    # page.pause()
    page.get_by_text("Existing Home").click()
    # page.pause()
    # page.get_by_text("Newly Constructed Home").click()
    # page.get_by_text("Commercial: Existing and New").click()
    # page.get_by_text("Existing Home").click()
    page.get_by_role("button", name="Next").click()
    # page.pause()
    # page.wait_for_load_state('domcontentloaded')
    # time.sleep(20)
    page.get_by_label("First Name").click()
    page.get_by_label("First Name").fill(payload.get('first_name'))
    # page.pause()
    page.get_by_label("Last Name").click()
    page.get_by_label("Last Name").fill(payload.get('last_name'))
    # page.pause()
    page.get_by_label("Please Enter Your Full").click()
    time.sleep(2)
    if payload.get('address').get("unit") != None and payload.get('address').get("unit") != null and payload.get('address').get("unit"):
      address_lookup = f"{payload.get('address').get("street")} {payload.get('address').get("unit")} {payload.get('address').get("city")} {payload.get('address').get("state")} {payload.get('address').get("zip")}"
      # unit =
    else:
      # address_lookup = f"{payload.get('address').get("street")}, {payload.get('address').get("city")} {payload.get('address').get("state")} {payload.get('address').get("zip")}"
      address_lookup = f"{payload.get('address').get("street")} {payload.get('address').get("city")} {payload.get('address').get("state")} {payload.get('address').get("zip")}"
    page.get_by_label("Please Enter Your Full").click()
    page.get_by_label("Please Enter Your Full").fill(address_lookup)
    # page.pause()
    try:
      time.sleep(2)
      page.locator(".pac-item-query").filter(has_text=f"{payload.get('address').get("street")}").first.click(timeout=1000)
      page.pause()
    except Exception as e:
      print("could not verify google address")
      try:
        page.get_by_label("Street address").click(force=True)
        page.get_by_label("Street address").fill(f"{payload.get('address').get("street")}")
        # page.pause()
        page.get_by_label("City").click()
        page.get_by_label("City").fill(f"{payload.get('address').get("city")}")
        # page.pause()
        page.get_by_label("Postal, Zip").fill(f"{payload.get('address').get("zip")}")
        page.get_by_label("Postal, Zip").click()
        page.get_by_label("State, Province").select_option(
          {payload.get('address').get("state")})
      except Exception as e:
        print("could not verify address")
        error = (f"could not verify google address: {payload.get('address').get("street")} {payload.get('address').get("unit")} {payload.get('address').get("city")} {payload.get('address').get("state")} {payload.get('address').get("zip")}")
    # page.pause()
    page.get_by_label("Phone").click()
    page.get_by_label("Phone").fill(payload.get('owner_phone') if payload.get(
      'owner_phone') != None else payload.get('installer_phone'))
    page.get_by_label("Owner Email").click()
    page.get_by_label("Owner Email").fill(payload.get('owner_email') if payload.get(
      'owner_email') != None else payload.get('installer_email'))
    # page.pause()
    page.get_by_label("Dealer Email").click()
    # page.pause()
    page.get_by_label("Dealer Email").press("ControlOrMeta+a")
    # page.pause()
    page.get_by_label("Dealer Email").fill(payload.get('installer_email'))

    # page.get_by_label("Equipment Eligibility").locator("div").filter(has_text="Equipment Eligibility").nth(1).click()
    # page.get_by_text("Close").click()
    # page.get_by_text("I have reviewed the").click()
    # page.get_by_label("Equipment Eligibility").get_by_label("Close").click()
    # page.get_by_text("I have reviewed the").click()
    # page.get_by_text("Close").click()
    # page.get_by_text("I have reviewed the").click()
    # page.get_by_label("Equipment Eligibility").get_by_label("Close").click()
    # page.pause()
    page.locator("#agree").click(force=True)
    # page.pause()
    # page.get_by_label("Equipment Eligibility").get_by_label("Close").click()
    # page.pause()
    time.sleep(5)
    page.get_by_role("button", name="Next").click(timeout=5000)
    try:
      page.get_by_text("Please provide a street").click(timeout=2000)
      page.get_by_label("Street address").click(force=True)
      page.get_by_label("Street address").fill(f"{payload.get('address').get("street")}")
      # page.pause()
      page.get_by_label("City").click()
      page.get_by_label("City").fill(f"{payload.get('address').get("city")}")
      # page.pause()
      page.get_by_label("Postal, Zip").fill(f"{payload.get('address').get("zip")}")
      page.get_by_label("Postal, Zip").click()
      page.get_by_label("State, Province").select_option(
        {payload.get('address').get("state")})
    except Exception as e:
      print("address entered")
    # page.pause()
    try:
      # page.pause()
      page.get_by_text("Suggested Address(es)").click(timeout=5000)
      suggested_address = page.locator(
        '#suggested-address-list').click(timeout=5000)
      # page.pause()
      # suggested_address.get_by_role('input').click()
      # page.pause()
      page.get_by_role("button", name="Continue").click(force=True)

    except Exception as e:
      print(f"something bad happened: {e}")
    finally:
      systems = payload.get('equipment')
      for system in systems:
        equipments = system.get('equipment')
        page.get_by_text("Tell Us About The Equipment").click(timeout=2000)
        # time.sleep(20)
        for equipment in equipments:
          # page.pause()
          page.get_by_label("Serial Number", exact=True).click(timeout=2000)
          page.get_by_label("Serial Number", exact=True).fill(
            equipment.get('serial_number'))
          # page.pause()
          page.get_by_placeholder("mm/dd/yyyy").click(timeout=2000)
          time.sleep(2)
          # page.pause()
          page.get_by_placeholder(
            "mm/dd/yyyy").fill(payload.get('install_date'))
          time.sleep(2)
          page.get_by_placeholder("mm/dd/yyyy").press("Enter")
          # page.get_by_role("heading", name="Tell Us About The Equipment").click()
          # page.pause()
          # try:
          #   page.locator("#addSerialButton").click(force=True)
          # except Exception as e:
          #   print(e)
          #   return e
          # page.pause()
          #
          # time.sleep(2)
          # page.get_by_role("button", name="Add").click(force=True)
          # xpage.pause()

          # check to see if serial number is registered
          print("checking to see if serial number is already registered")
          try:
            page.get_by_text(
              "This serial number is previously registered and cannot be registered again").click(timeout=2000)
            error = (
              f"Serial number previously registered: {equipment.get('serial_number')}")
            print(
              f"Serial number previously registered: {equipment.get('serial_number')}")
            return error
          except Exception as e:
            print("serial number not registered")

          # check to see if non serialized item
          print("checking to see if non serialized item")
          try:
            page.locator('#nonSerialInputForm').click(timeout=2000)
            page.pause()
            if equipment.get('warranty_model') != None and equipment.get('warranty_model') != null:
              warranty_model = equipment.get('warranty_model')
              # page.pause()
              optionToSelect = page.locator(
                'option', has_text=f'{warranty_model}').text_content()
              print(optionToSelect)
              page.get_by_label("Product Type").select_option(optionToSelect)
              # page.pause()
              page.get_by_label("Brand").select_option("Lennox")
              page.get_by_placeholder("Enter Model").click()
              page.get_by_placeholder("Enter Model").fill(f"{warranty_model}")
              page.locator("#addNonSerialAddButton").click()
            # Heat Strips
            elif equipment.get('type_id') == 115:
              warranty_model = None
              for parent_equipment in equipments:
                if parent_equipment.get('warranty_model') != None and parent_equipment.get('warranty_model') != null:
                  warranty_model = parent_equipment.get('warranty_model')
                  optionToSelect = page.locator(
                    'option', has_text=f'{warranty_model}').text_content()
                  print(optionToSelect)
                  page.get_by_label(
                    "Product Type").select_option(optionToSelect)
                  # page.pause()
                  page.get_by_label("Brand").select_option("Lennox")
                  page.get_by_placeholder("Enter Model").click()
                  page.get_by_placeholder("Enter Model").fill(
                    f"{equipment.get('model')}")
                  page.locator("#addNonSerialAddButton").click()
                  break
                else:
                  continue
              if warranty_model:
                print("found heat strip model")
              else:
                print(f"no warranty model for: {equipment.get('model')}")
                error = f"no warranty model for: {equipment.get('model')}"
                return error
            # Dampers
            elif equipment.get('type_id') == 50 or equipment.get('type_id') == 181 or equipment.get('type_id') == 8:
              optionToSelect = page.locator(
                'option', has_text="Dampers").first.text_content()
              print(optionToSelect)
              page.get_by_label("Product Type").select_option(optionToSelect)
              # page.pause()
              page.get_by_label("Brand").select_option("Lennox")
              page.get_by_placeholder("Enter Model").click()
              page.get_by_placeholder("Enter Model").fill(
                f"{equipment.get('model')}")
              page.locator("#addNonSerialAddButton").click()
            else:
              print(f"no warranty model for: {equipment.get('model')}")
              error = f"no warranty model for: {equipment.get('model')}"
              return error
          except Exception as e:
            print(f"something bad happened: {e}")

          # check to see if serial number was submitted correctly
          print("checking to see if serial number was submitted correctly")
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
      page.get_by_role("button", name="Next").click()
      # Check to see if lennox warranty is down
      # page.pause()
      # Section to select coil matches
      print("Looking for coil pairings")
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
                has_text=f'{equipment.get("serial_number")}').click(timeout=2000)
              coil_pairing.locator('select').click(timeout=2000)
              # coil_pairing=page.get_by_text(f'{equipment.get("serial_number")}').click(timeout=2000)
              # coil_pairing.locator(f'#{equipment.get("serial_number")}').click(timeout=2000)
              for coil in equipments:
                try:
                  # page.pause()
                  option_to_select = coil_pairing.locator("option").filter(has_text=f"{coil.get("serial_number")}").first.text_content()
                  coil_pairing.locator(
                    'select').select_option(option_to_select)
                  # page.locator("option").filter(has_text=f"{coil.get("serial_number")}").first.click(timeout=5000)
                  break
                except Exception as e:
                  print(f"could not find coil pairing: {coil.get("serial_number")}")
            except Exception as e:
              print(f"could not find AC Unit pairing: {equipment.get("serial_number")}")
          coil_number += 1
        page.get_by_role("button", name="Next").click(timeout=2000)

      except Exception as e:
        print("no coil pairings")

      # <select class="pairing-coil form-control" onfocus="onCoilSelectFocus(this)" onchange="onCoilSelect(this)" id="5824H01302" required=""> <option selected="" value="" class="option-background">Select pairing coil</option><option value="skip-pairing" class="option-background">Skip pairing</option><option value="1524H04108-2024-09-10" class="OneLinkNoTx option-background ">1524H04108 - CK40CT-60C Coil 5.0 Ton R410A/R454B - 09/09/2024</option><option value="1524H04106-2024-09-10" class="OneLinkNoTx option-background ">1524H04106 - CK40CT-60C Coil 5.0 Ton R410A/R454B - 09/09/2024</option></select>

      # #ac-group-title
      # .equipment-rows
      # page.pause()
      try:
        page.get_by_role(
          "heading", name="Warranty Your Way is").click(timeout=5000)
        error = "Lennox site is NOT working"
        print("Lennox site is NOT working")
        return error
      except Exception as e:
        print("Lennox site is working")

      # Section to select coil matches
      try:
        page.get_by_role("button", name="Next").click()
      # page.pause()
      except Exception as e:
        print(f"something bad happened: {e}")

      select_all_warranties = False
      while select_all_warranties == False:
        try:
          page.get_by_text("$000.00").click(timeout=2000)
          page.get_by_role("button", name="Select").click()
        except Exception as e:
          try:
            page.get_by_role("button", name="Select").click(timeout=2000)

          except Exception as e:
            print(f"something bad happened: {e}")
            print(f"something bad happened: {e}")
            break
      all_equipment_reviewed = False
      while all_equipment_reviewed == False:
        try:
          page.get_by_role("button", name="Review Next").click(timeout=2000)
        except Exception as e:
          print("all equipment has been reviewed")
          break

      try:
        page.get_by_role(
          "heading", name="Warranty Your Way is").click(timeout=5000)
        error = "Lennox site is NOT working"
        print("Lennox site is NOT working")
        return error
      except Exception as e:
        print("Lennox site is working")
      # page.pause()
      try:
        page.locator("#lii-terms").click(force=True)
        page.locator("#lii-terms").click(force=True)
        page.locator("#lii-terms").click(force=True)
        # page.pause()
      except Exception as e:
        print("couldn't click terms")
      page.pause()
      page.get_by_role("button", name="Submit & Checkout").click()
      # page.pause()
      page.get_by_text("Submit & Checkout Please").click()
      # page.pause()
      page.get_by_label("Submit & Checkout Please").get_by_role(
        "button", name="Submit & Checkout").click(force=True)
      time.sleep(5)
      with page.expect_download() as download_info:
        page.get_by_role("link", name="View/Download Registration").click()
      download = download_info.value
      file_name = urllib.parse.quote(
        f"lennox_warranty_{payload.get('first_name')}_{payload.get('last_name')}_{payload.get('st_job_id')}.pdf").lower()
      print(file_name)
      print("saving download")
      download.save_as(Path.home().joinpath('Downloads', file_name))

      # download.save_as(download.suggested_filename)

    # ---------------------
    context.close()
    browser.close()

  with sync_playwright() as playwright:
    run(playwright)


# Trane
def registerTrane(payload):

  from playwright.sync_api import Playwright, sync_playwright

  def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    # browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    download = None

    page.goto(
      "https://warrantyregistration.tranetechnologies.com/wrApp/index.html#/trane/welcome")
    # page.get_by_text("Commercial").click()
    # page.get_by_role("radio").nth(1).check()
    # page.get_by_role("radio").first.check()
    # page.pause()
    if payload.get('type') == "Residential":
      page.get_by_role("radio").first.check()
    elif payload.get('type') == "Commercial":
      page.get_by_role("radio").nth(1).check()
    else:
      error = ("Unknown customer type")
      print("Unknown customer type")
      return error
    # page.get_by_text("Commercial").click()
    # page.get_by_text("Residential Commercial").click()
    # page.get_by_role("radio").nth(1).check()
    # page.get_by_role("radio").first.check()
    if payload.get('address').get("unit") != None and payload.get('address').get("unit"):
      unit = payload.get('address').get("unit")
    else:
      unit = ""

    page.get_by_placeholder("Enter First Name").click()
    page.get_by_placeholder("Enter First Name").fill(payload.get('first_name'))
    page.get_by_placeholder("Enter Last Name").click()
    page.get_by_placeholder("Enter Last Name").fill(payload.get('last_name'))
    page.get_by_placeholder("Enter Address Line 1").click()
    page.get_by_placeholder("Enter Address Line 1").fill(f"{payload.get('address').get("street")} {(payload.get('address').get("unit")) if (payload.get('address').get("unit")) != None else ""} {payload.get('address').get("city")} {payload.get('address').get("state")} {payload.get('address').get("zip")}")
    # page.pause()
    try:
      time.sleep(2)
      page.pause()
      address_dropdown = page.get_by_role('listbox')
      # address_dropdown.locator('li').locator('a').nth(1).click()
      address_dropdown.locator('li').locator(
        'a').filter(has_not_text="#").first.click()
      if payload.get('address').get("unit") != None and payload.get('address').get("unit"):
        page.pause()
        # unit_selector = page.get_by_placeholder("Select Unit")
        unit_selector = page.locator(
          "[model='contactData.equipmentAddress.address2'] >> visible=true")
        unit_selector.click()
        print(unit_selector)
        optionToSelect = unit_selector.locator('select').locator('option', has_text=f'{payload.get('address').get("unit")}').text_content()
        print(optionToSelect)
        unit_selector.locator('select').select_option(optionToSelect)
        # page.pause()
    except Exception as e:
      print("could not verify address with google")
      page.pause()
      try:
        page.get_by_placeholder("Enter Address Line 1").fill(
          payload.get('address').get("street"))
        if payload.get('address').get("unit") != None and payload.get('address').get("unit"):
          page.get_by_placeholder("Enter Address Line 2 (Example").fill(
            payload.get('address').get("unit"))
        page.locator("#lCity").fill(payload.get('address').get("city"))
        page.locator("#lState").select_option(
          payload.get('address').get("state"))
        page.locator("input[name=\"pZip\"]").fill(
          payload.get('address').get("zip"))
      except Exception as e:
        print("could not verify address manually")
        error = "could not verify address manually"
        return error
    # address_dropdown.select_option(index=0)

    # # page.get_by_role("option", name=f"{payload.get('address').get("street")} {(payload.get('address').get("unit")) if (payload.get('address').get("unit")) != None else ""} {payload.get('address').get("city")} {payload.get('address').get("state")} {payload.get('address').get("zip")}").click()
    # page.pause()

    #  page.get_by_placeholder("Enter Address Line 2").click()
    #  page.get_by_placeholder("Enter Address Line 2").fill(f"{payload.get('address').get("unit")}")
    page.get_by_placeholder("Enter Phone Number").click()
    page.get_by_placeholder("Enter Phone Number").fill(payload.get(
      'owner_phone') if payload.get('owner_phone') != None else payload.get('installer_phone'))
    # page.pause()
    page.get_by_placeholder("Enter Email").click()
    page.get_by_placeholder("Enter Email").fill(payload.get('owner_email') if payload.get(
      'owner_email') != None else payload.get('installer_email'))
    # page.pause()
    page.get_by_placeholder("Enter Dealer / Builder Name").click()
    page.get_by_placeholder(
      "Enter Dealer / Builder Name").fill(payload.get('installer_name'))
    # page.pause()
    page.get_by_placeholder("Enter Dealer / Builder Phone").click()
    page.get_by_placeholder(
      "Enter Dealer / Builder Phone").fill(payload.get('installer_phone'))
    # page.pause()
    page.get_by_placeholder("Enter Dealer / Builder Email").click()
    page.get_by_placeholder(
      "Enter Dealer / Builder Email").fill(payload.get('installer_email'))
    # page.pause()
    page.get_by_role("button", name="Continue").click(timeout=2000)
    try:
      page.get_by_text("Verify your Home owner/").click()
      page.get_by_role("button", name="Continue").click()
      # page.get_by_role("button", name="Continue").click()
    except Exception as e:
      print("didnt need to verify address")
    # page.pause()
    page.locator("div").filter(
      has_text="Components Components Search").nth(1).click()
    # page.pause()
    time.sleep(2)
    equipments = payload.get('equipment')
    systems = payload.get('equipment')
    system_number = 1
    for system in systems:
      equipments = system.get('equipment')
      if system_number > 1:
        # page.pause()
        page.locator("#newSystem").click()
        page.get_by_role("heading", name="Add New System").click()
        page.get_by_placeholder("Enter system name").click()
        page.get_by_placeholder("Enter system name").fill(
          f"System{system_number}")
        page.get_by_role("button", name="Add").nth(1).click()
        page.locator(f"#systemRow-{system_number-1}").click()
        # page.get_by_text(f"System{system_number} Click to edit system").click(force=True)
      for equipment in equipments:
        # page.pause()
        page.get_by_placeholder("Enter your serial number").click()
        page.get_by_placeholder("Enter your serial number").fill(
          equipment.get('serial_number'))
        # Check to see if unit is registered
        try:
          page.get_by_text(
            "This unit has already been registered").click(timeout=2000)
          page.get_by_text(
            "is associated to another active registration.").click(timeout=2000)
          error = (
            f"Serial number previously registered: {equipment.get('serial_number')}")
          print(
            f"Serial number previously registered: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print("serial number not registered")
        page.get_by_role("button", name="Add").click()
        # Check to see if unit is eligible
        try:
          page.get_by_text(
            "Serial Number not eligible").first.click(timeout=2000)
          error = (
            f"Serial number not eligible for registration: {equipment.get('serial_number')}")
          print(
            f"Serial number not eligible for registration: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print("serial number is eligible")
        # Check to see if unit serial is correct
        try:
          page.get_by_text(
            "(Error during serial number").first.click(timeout=2000)
          error = (
            f"Error with serial number: {equipment.get('serial_number')}")
          print(f"Error with serial number: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print("serial number is correct")
        page.pause()
        try:
          page.get_by_text("Component validation failed").click(timeout=2000)
          error = (
            f"Error with serial number: {equipment.get('serial_number')}")
          print(f"Error with serial number: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print("serial number is correct")
        page.get_by_text("Install Date (MM/DD/YYYY):").first.click()
        page.get_by_role(
          "heading", name="Serialized Components", exact=True).click()
        page.get_by_role("textbox", name="MM/DD/YYYY").click()
        page.get_by_role(
          "textbox", name="MM/DD/YYYY").fill(payload.get('install_date'))
        # page.pause()
        page.get_by_role("button", name="Add").nth(1).click()

        # page.pause()
        components_table = page.locator('#componentTable')
        print(components_table)
        # page.pause()
        serial_number_found = components_table.get_by_text(
          f"{equipment.get('serial_number')}")
        print(serial_number_found.text_content())
      system_number += 1
    # page.pause()
    page.get_by_role("button", name="Continue").click()
    # page.pause()
    page.get_by_role("button", name="Complete Registration").click()
    # page.pause()
    time.sleep(5)
    with page.expect_download() as download_info:
      page.get_by_role("button", name="View Warranty Certificate").click()
    download = download_info.value
    # page.pause()
    # page.emulate_media(media="screen")
    file_name = urllib.parse.quote(
      f"trane_warranty_{payload.get('first_name')}_{payload.get('last_name')}_{payload.get('st_job_id')}.pdf").lower()
    print("saving download")
    download.save_as(Path.home().joinpath('Downloads', file_name))
    # pdf = page.pdf(path=file_name)
    # pdf.save_as(Path.home().joinpath('Downloads', file_name))
    # print(file_name)
    # print("saving download")
    # download.save_as(Path.home().joinpath('Downloads', file_name))

    # print(pdf)
    # print(download)

    # if download is not(None):
    #   temp_file = NamedTemporaryFile(delete=True)
    #   download.save_as(temp_file.name)
    #   temp_file.flush()
    #   pdf = files.File(temp_file)

    # encoded_pdf = None
    # if pdf is not(None):
    #   with open(pdf.name, "rb") as pdf:
    #     encoded_pdf = base64.b64encode(pdf.read())
    #   r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/warranty_upload', data={"st_jobs_id": payload.get('st_job_id') , "companies_id": payload.get('companies_id'), "manufacturer": "Trane", "warranty": encoded_pdf, "needs_review": False, "warranty_review_reason": None}, timeout=30)
    #   print(r)

    # with page.expect_download() as download_info:
    #     with page.expect_popup() as page1_info:
    #         page.get_by_role("button", name="View Warranty Certificate").click()
    #     page1 = page1_info.value
    # download = download_info.value
    # ---------------------
    context.close()
    browser.close()

  with sync_playwright() as playwright:
    run(playwright)


def registerDaikin(payload):
  print(payload)

  from playwright.sync_api import Playwright, sync_playwright

  def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    # browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    error = False
    download = None
    page.goto("https://warranty.goodmanmfg.com/newregistration/")
    # page.goto("https://warranty.goodmanmfg.com/newregistration/#/reg-layout")
    # equipments = payload.get('equipment')
    systems = payload.get('equipment')
    for system in systems:
      equipments = system.get('equipment')
      for equipment in equipments:
        page.get_by_role("textbox", name="Serial number").click(timeout=2000)
        page.get_by_role("textbox", name="Serial number").fill(
          equipment.get('serial_number'))
        page.get_by_text("1Product Info2Customer").click()
        # page.pause()
        try:
          page.get_by_text(
            "This unit has already been registered").click(timeout=2000)
          error = (
            f"Serial number previously registered: {equipment.get('serial_number')}")
          print(
            f"Serial number previously registered: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print("serial number not registered")
        # page.pause()
        try:
          page.get_by_role(
            "cell", name=f"{equipment.get('serial_number')}").click(timeout=5000)
          print(page.get_by_role("cell", name=f"equipment.get('serial_number')"))
        except Exception as e:
          print(
            f"Serial number could not be added: {equipment.get('serial_number')}")
          try:
            page.get_by_role("combobox", name="Number").click()
            page.get_by_role("combobox", name="Number").fill(
              equipment.get('model'))
            page.get_by_role("option", name=equipment.get('model')).click()
            page.get_by_role("button", name="Add Serial").click()
          except Exception as e:
            print(
              f"Serial number could not be added with model number: {equipment.get('model')}")
            error = f"Serial number ({equipment.get('serial_number')}) could not be added with model number ({equipment.get('model')})"
            page.pause()
            return error
        # page.pause()
    page.locator("[formcontrolname='installDate'] >> visible=true").fill(
      payload.get('install_date'))
    # print('here')
    # page.pause()
    if payload.get('type') == "Residential":
      page.get_by_text("Residential(Owner Occupied").click()
    elif payload.get('type') == "Commercial":
      page.get_by_text("Commercial").click()
    else:
      error = ("Unknown customer type")
      print("Unknown customer type")
      return error
    # page.locator("#mat-radio-6 > .mat-radio-label > .mat-radio-container").click()
    page.pause()
    page.get_by_role("button", name="Next").click()
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("textbox", name="First Name").click()
    page.get_by_role("textbox", name="First Name").fill(
      payload.get('first_name'))
    page.get_by_role("textbox", name="Last Name").click()
    page.get_by_role("textbox", name="Last Name").fill(
      payload.get('last_name'))
    page.get_by_role("textbox", name="Phone").click()
    page.get_by_role("textbox", name="Phone").fill(payload.get('owner_phone') if payload.get(
      'owner_phone') != None and payload.get('owner_phone') != null else payload.get('installer_phone'))
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill(payload.get('owner_email') if payload.get(
      'owner_email') != None and payload.get('owner_email') != null else payload.get('installer_email'))
    page.get_by_label("Zip/Postal Code *").click()
    page.get_by_label(
      "Zip/Postal Code *").fill(payload.get('address').get("zip"))
    page.locator("reg-layout").click()
    page.get_by_role("textbox", name="Address1").click()
    page.get_by_role("textbox", name="Address1").fill(
      payload.get('address').get("street"))
    if payload.get('address').get("unit") != None and payload.get('address').get("unit") != null:
      page.get_by_role("textbox", name="Address2").click()
      page.get_by_role("textbox", name="Address2").fill(
        payload.get('address').get("unit"))
    # page.pause()
    page.get_by_role("button", name="Next").click()
    page.pause()
    try:
      page.get_by_role("cell", name="Recommended Address").click(timeout=2000)
      page.get_by_role("button", name="Use address recommended").click()
    except Exception as e:
      print("did not verify address")
    # page.pause()
    page.get_by_role("textbox", name="Dealer/Builder*").click()
    page.get_by_role(
      "textbox", name="Dealer/Builder*").fill(payload.get('installer_name'))
    page.get_by_role("textbox", name="Dealer/Builder Phone*").click()
    page.get_by_role(
      "textbox", name="Dealer/Builder Phone*").fill(payload.get('installer_phone'))
    page.pause()
    page.get_by_role("button", name="Register").click()
    try:
      page.get_by_text("Please confirm the name/").click(timeout=2000)
      page.get_by_role("button", name="Yes").click()
    except Exception as e:
      print("no dialog to confirm address after registration")
    try:
      page.get_by_text("Congratulations! This product").click(timeout=2000)
      page.pause()
      page.get_by_role("button", name="Affirm", exact=True).click(force=True)
      page.get_by_text("Please confirm the name/").click(force=True)
      page.get_by_role("button", name="Yes").click(force=True)
    except Exception as e:
      print(f"something went wrong: {e}")
    page.pause()
    try:
      page.locator(".swal-modal").click(timeout=3000)
      modal = page.locator(".swal-modal")
      print("clicked modal")
      # modal.locator("div").filter(has_text="OK").click()
      modal.get_by_text("OK").click()
      print("clicked ok")
      page.get_by_label("Close").click()
      print("closed modal")
      # modal.get_by_role("button", name="OK").click(force=True)
      # page.locator(".cdk-overlay-backdrop").click(force=True)
      # page.locator(".cdk-overlay-backdrop").click(force=True)
      page.locator("div").filter(has_text="Please register your").first.click()
      page.locator("div").filter(has_text="Please register your").first.click()
      page.get_by_role("button", name="OK").click(timeout=2000)
    except Exception as e:
      print("something went wrong")
    page.pause()
    time.sleep(2)
    with page.expect_download() as download_info:
      print(page.get_by_role("button", name="Download Certificate"))
      page.get_by_role("button", name="Download Certificate").click(
        force=True, timeout=2000)
    download = download_info.value
    file_name = urllib.parse.quote(
      f"daikin_warranty_{payload.get('first_name')}_{payload.get('last_name')}_{payload.get('st_job_id')}.pdf").lower()
    print(download)
    print(file_name)
    print("saving download")
    download.save_as(Path.home().joinpath('Downloads', file_name))

    # ---------------------
    context.close()
    browser.close()

  with sync_playwright() as playwright:
    run(playwright)


def registerCarrier(payload):
  print(payload)

  from playwright.sync_api import Playwright, sync_playwright

  def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    error = False
    download = None
    page.goto(
      "https://productregistration.carrier.com/public/RegistrationForm_Carrier?brand=CARRIER")
    page.locator("#Products_0__SerialNumber").fill("2524V61940")
    page.locator("#Products_0__SerialNumber").click()
    page.locator("div").filter(
      has_text="PRODUCT REGISTRATION 1 Serial").nth(1).click()
    page.get_by_role("row", name="2524V61940 KFFEH2601C10").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="2524V61940 KFFEH2601C10").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="2524V61940 KFFEH2601C10").get_by_placeholder(
      "MM/DD/YYYY").fill("09/28/2024")
    page.locator("div").filter(
      has_text="PRODUCT REGISTRATION 1 Serial").nth(1).click()
    page.locator("#Products_1__SerialNumber").click()
    page.locator("#Products_1__SerialNumber").fill("3024C62073")
    page.locator("#Products_1__SerialNumber").click()
    page.get_by_role("row", name="3024C62073 Refresh").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="3024C62073 GA5SAN43600W").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="3024C62073 GA5SAN43600W").get_by_placeholder(
      "MM/DD/YYYY").fill("09/28/2024")
    page.get_by_role("row", name="Refresh", exact=True).get_by_placeholder(
      "Enter serial number").click()
    page.get_by_role("row", name="Refresh", exact=True).get_by_placeholder(
      "Enter serial number").fill("2624F03703")
    page.get_by_role("row", name="Refresh", exact=True).get_by_placeholder(
      "Enter serial number").click()
    page.get_by_role("row", name="2624F03703 FJ4DNXB36L00").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="2624F03703 FJ4DNXB36L00").get_by_placeholder(
      "MM/DD/YYYY").fill("9/28/2024")
    page.locator("div").filter(
      has_text="PRODUCT REGISTRATION 1 Serial").nth(1).click()
    page.get_by_role("img", name="Delete").click()
    page.get_by_role(
      "row", name="2624F03703 FJ4DNXB36L00 9/28/").get_by_placeholder("MM/DD/YYYY").dblclick()
    page.get_by_role("link", name="28").click()
    page.get_by_label("Replacement of existing").check()
    page.get_by_label("Replacement of existing").check()
    page.get_by_label("Residential Single Family").check()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_role("button", name="Next", exact=True).click()
    page.get_by_placeholder("Enter first name").click()
    page.get_by_placeholder("Enter first name").fill("Tige Brown")
    page.get_by_placeholder("Enter first name").click()
    page.get_by_placeholder("Enter first name").click()
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("ControlOrMeta+x")
    page.get_by_placeholder("Enter first name").fill("Tige")
    page.get_by_placeholder("Enter last name").click()
    page.get_by_placeholder("Enter last name").fill("Brown")
    page.get_by_role("textbox", name="Enter address", exact=True).click()
    page.get_by_role("textbox", name="Enter address", exact=True).fill(
      "4045 North Indigo Drive, Harvey, LA 70058")
    page.get_by_role("textbox", name="Enter address", exact=True).click()
    page.locator("#ui-id-10").click()
    page.get_by_label("Check here if you don't have").check()
    page.get_by_label("Check here if you don't have").uncheck()
    page.locator("#txtConsumerEmail").click()
    page.locator("#txtConsumerEmail").click()
    page.locator("#txtConsumerConfirmEmail").click()
    page.locator("#txtConsumerConfirmEmail").click()
    page.get_by_label("Check here if you don't have").check()
    page.get_by_label("Check here if your address is").check()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_role("textbox", name="(999) 999-").click()
    page.get_by_role(
      "textbox", name="(999) 999-").fill("(2258036441___) ___-____")
    page.locator("#webcontent1").click()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_role("textbox", name="Enter address", exact=True).click()
    page.get_by_role("textbox", name="Enter zip code").click()
    page.get_by_text("Step 3 of 6: Equipment").click()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_text("Step 4 of 6: DEALER").click()
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("textbox", name="Please contact your").fill("Keefes")
    page.get_by_role("button", name=" Search").click()
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("textbox", name="Please contact your").fill("Keefe")
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("button", name=" Search").click()
    page.get_by_text("MFG Account # 181418-").click()
    page.get_by_text("MFG Account # 181418-").click(click_count=5)
    page.get_by_text("MFG Account # 181418-").dblclick()
    page.get_by_text("MFG Account # 181418-").click()
    page.get_by_label("Keefe's A/C & Heating Inc").check()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_text("Step 5 of 6: Warranty Details").click()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_text("Step 6 of 6: Review & Submit").click()
    page.get_by_role("button", name="Submit   ").click()
    page.get_by_role("button", name="Yes").click()
    page.get_by_role("button", name="PRINT   ").click()
    page.get_by_text("Z006215691190C").click()

    # ---------------------
    context.close()
    browser.close()

  with sync_playwright() as playwright:
    run(playwright)


@celery_app.task
def register_warranties(payload):
  # print(payload)
  warranty = None
  # Filter out non-installs
  filtered_data = filter_equipment_by_install_date(payload)
  print(filtered_data)

  # # Group equuipment by manufacturer
  # grouped_equipment = group_equipment_by_manufacturer(filtered_data)

  grouped_equipment = group_equipment_by_manufacturer_and_system(filtered_data)
  # print(grouped_equipment)
  # return grouped_equipment

  # Lennox Registrations
  lennox_equipment = get_equipment_by_manufacturer_id(grouped_equipment, [22])
  print(lennox_equipment)
  if lennox_equipment:
    lennox_payload = payload
    lennox_payload['equipment'] = lennox_equipment
    print(lennox_payload)
    warranty = registerLennox(lennox_payload)

  # Trane Registrations
  trane_equipment = get_equipment_by_manufacturer_id(grouped_equipment, [1])
  # print(trane_equipment)
  if trane_equipment:
    trane_payload = payload
    trane_payload['equipment'] = trane_equipment
    print(trane_payload)
    registerTrane(trane_payload)

  # Daikin Registrations
  daikin_equipment = get_equipment_by_manufacturer_id(
    grouped_equipment, [49, 33])
  # print(trane_equipment)
  if daikin_equipment:
    daikin_payload = payload
    daikin_payload['equipment'] = daikin_equipment
    print(registerDaikin)
    warranty = registerDaikin(daikin_payload)

  return warranty


runWarrantyRegistration(payload)

# registerDaikin(payload)
# getTraneWarranty("4095Y195G", True, None, None, None)
