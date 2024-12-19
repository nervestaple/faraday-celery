import time

from typing import Union
from s3 import upload_warranty_pdf_to_s3
from scrape import scrape
from playwright.sync_api import Page


def register_carrier_warranty(payload, systems) -> tuple[Union[str, None], Union[str, None]]:
  log_context = {'job_id': payload['job_id'], 'manufacturer_name': 'carrier'}

  carrier_dealer_code = payload.get('carrier_dealer_code')
  if not carrier_dealer_code:
    error = 'Carrier dealer code is required'
    print(error, log_context)
    return None, error

  address_type = payload.get('type')

  def scraper(page: Page) -> tuple[Union[str, None], Union[str, None]]:
    page.goto(
      "https://productregistration.carrier.com/Dealer/RegistrationForm?brand=CARRIER")

    page.locator('#txtDealerInput').click()
    page.locator('#txtDealerInput').fill(carrier_dealer_code)
    page.locator('#btnFindDealer').click()

    page.wait_for_load_state('networkidle')

    page.locator('#SelectDealer').click()
    page.locator('#wizard-next').click()

    page.wait_for_load_state('networkidle')
    page.wait_for_selector('.dvSpinner', state='hidden')

    all_equipment = [
      equipment_item for system_equipment in systems for equipment_item in system_equipment]

    for index, equipment_item in enumerate(all_equipment):
      error = fill_equipment_item(page, index, equipment_item)
      if error:
        print(error, log_context)
        return None, error

    page.get_by_label("Replacement of existing").check()

    if address_type == "Commercial":
      page.get_by_label("Commercial").check()
    else:
      page.get_by_label("Residential Single Family").check()

    page.get_by_label("Replacement of existing equipment").check()

    fill_address(page, payload)

    page.get_by_role("button", name="Continue").click()

    page.wait_for_load_state('networkidle')
    page.wait_for_selector('.dvSpinner', state='hidden')

    serial_error_messages = page.locator(
      '.SerialErrorDisplay').filter(has_text=' ').all_inner_texts()

    if any(serial_error_messages):
      errors_with_serials = [f"{all_equipment[i].get('serial_number')}: {error}"
                             for i, error in enumerate(serial_error_messages) if error]
      joined = ', '.join(errors_with_serials)
      error = f"Serial number errors -- {joined}"
      print(error, log_context)
      return None, error

    try:
      page.get_by_role("button", name="OK").click(force=True)

      page.wait_for_load_state('networkidle')
      page.wait_for_selector('.dvSpinner', state='hidden')

      page.get_by_role("button", name="Continue").click()

      page.wait_for_load_state('networkidle')
      page.wait_for_selector('.dvSpinner', state='hidden')
    except Exception as e:
      pass

    page.get_by_label("No labor coverage desired.").check()

    page.get_by_label(
      "I have reviewed and agree to the  Climate Shield ESA Program Enrollment Terms & Conditions.").check()

    page.pause()

    page.get_by_role("button", name="SUBMIT").click()
    page.get_by_role("button", name="Yes").click(force=True)
    page.wait_for_load_state('networkidle')
    page.wait_for_selector('.dvSpinner', state='hidden')

    page.pause()

    pdf_bytes = page.pdf()

    uploaded_pdf_path = upload_warranty_pdf_to_s3(
      pdf_bytes, {'job_id': payload['job_id'], 'manufacturer_name': 'carrier'})

    print('uploaded_pdf_path:', uploaded_pdf_path, log_context)
    return uploaded_pdf_path, None

  return scrape(scraper)


def fill_equipment_item(page: Page, index, equipment_item):
  serial_number = equipment_item.get('serial_number')
  installation_date = equipment_item.get('installed_on')

  serial_input = page.locator(f'#Products_{index}__SerialNumber')
  serial_input.click()
  serial_input.fill(serial_number)
  serial_input.blur()

  page.wait_for_load_state('networkidle')

  model_input = page.locator(f'#Products_{index}__SelectedModel')
  model_input.focus()
  model_input.blur()

  serial_error = serial_input.locator('..').locator('.SerialErrorDisplay')
  if serial_error.is_visible():
    serial_error_text = serial_error.inner_text()
    error = f"Serial number error for {serial_number}: {serial_error_text}"
    return error

  install_date_input = page.locator(f'#Products_{index}__InstallationDate')
  install_date_input.click()
  install_date_input.fill(installation_date)
  install_date_input.blur()

  page.wait_for_load_state('networkidle')


def fill_address(page: Page, payload):
  first_name = payload.get('first_name')
  last_name = payload.get('last_name')

  address = payload.get('address')
  address_street = address.get('street')
  address_unit = address.get('unit')
  address_city = address.get('city')
  address_state = address.get('state')
  address_zip = address.get('zip')

  owner_email = payload.get('owner_email')
  owner_phone = payload.get('owner_phone')
  installer_email = payload.get('installer_email')
  installer_phone = payload.get('installer_phone')

  owner_phone = owner_phone if owner_phone else installer_phone
  owner_email = owner_email if owner_email else installer_email

  page.get_by_placeholder("Enter first name").click()
  page.get_by_placeholder("Enter first name").fill(first_name)

  page.get_by_placeholder("Enter last name").click()
  page.get_by_placeholder("Enter last name").fill(last_name)

  street_input = page.get_by_role("textbox", name="Enter address", exact=True)
  street_input.click()
  street_input.fill(address_street)

  if address_unit:
    unit_input = page.get_by_role("textbox", name="Enter address line 2")
    unit_input.click()
    unit_input.fill(address_unit)

  city_input = page.get_by_role("textbox", name="Enter city")
  city_input.click()
  city_input.fill(address_city)

  zip_input = page.get_by_role("textbox", name="Enter zip code")
  zip_input.click()
  zip_input.fill(address_zip)

  page.locator("#ddlConsumerState").select_option(address_state)
  page.locator("#ddlConsumerState").blur()

  page.locator('#txtConsumerPhone1').click()
  page.locator('#txtConsumerPhone1').fill(owner_phone)

  page.locator("#txtConsumerEmail").click()
  page.locator("#txtConsumerEmail").fill(owner_email)

  page.locator("#txtConsumerConfirmEmail").click()
  page.locator("#txtConsumerConfirmEmail").fill(owner_email)

  page.locator('#chkEquipOwnerAcknowledge').check()
