import time
from typing import Union
from playwright.sync_api import Page

from config import IS_DEV
from scrape import scrape
from s3 import upload_remote_warranty_pdf_to_s3


def register_trane_warranty(payload, systems) -> tuple[Union[str, None], Union[str, None]]:
  log_context = {'job_id': payload['job_id'], 'manufacturer_name': 'trane'}

  address_type = payload.get('type')
  address = payload.get('address')
  first_name = payload.get('first_name')
  last_name = payload.get('last_name')

  def scraper(page: Page) -> tuple[Union[str, None], Union[str, None]]:
    page.goto(
      'https://warrantyregistration.tranetechnologies.com/wrApp/index.html#/trane/welcome')

    print('Trane warranty registration page loaded', log_context)

    if address_type == 'Residential':
      page.get_by_role('radio').first.check()
    elif address_type == 'Commercial':
      page.get_by_role('radio').nth(1).check()
    else:
      error = ('Unknown customer type')
      print('Unknown customer type', log_context)
      return None, error

    page.get_by_placeholder('Enter First Name').click()
    page.get_by_placeholder('Enter First Name').fill(first_name)
    page.get_by_placeholder('Enter Last Name').click()
    page.get_by_placeholder('Enter Last Name').fill(last_name)

    auto_input_success = auto_address_input(page, address)
    if not auto_input_success:
      manual_address_input(page, address)

    extra_fields_input(page, payload)

    page.get_by_role('button', name='Continue').click(timeout=5000)

    print('Trane warranty registration page filled', log_context)

    time.sleep(2)
    if page.get_by_text('Verify your Home owner/').is_visible():
      print('verifying address', log_context)
      page.get_by_text('Verify your Home owner/').click()
      page.get_by_role('button', name='Continue').click()

    page.locator('div').filter(
      has_text='Components Components Search').nth(1).click()
    time.sleep(2)

    for index, system_equipment in enumerate(systems):
      system_number = index + 1
      if system_number > 1:
        add_system(page, system_number)

      for equipment_item in system_equipment:
        add_equipment_error = add_equipment_item(page, equipment_item)
        if add_equipment_error:
          return None, add_equipment_error

    page.get_by_role("button", name="Continue").click()
    page.pause()
    print("BEFORE COMPLETING TRANE REGISTRATION", log_context)
    page.get_by_role("button", name="Complete Registration").click()
    print(
      "SUCCESS COMPLETING TRANE REGISTRATION", log_context)

    if IS_DEV:
      with page.expect_popup() as popup_info:
        page.get_by_role('button', name='View Warranty Certificate').click()
        pdf_url = popup_info.value.url
        uploaded_pdf_url = upload_remote_warranty_pdf_to_s3(
          pdf_url, {'job_id': payload['job_id'], 'manufacturer_name': 'trane'})
        return uploaded_pdf_url, None
      return None, 'Popup not found'

    with page.expect_download() as download_info:
      page.pause()
      page.get_by_role('button', name='View Warranty Certificate').click()
      print('DOWNLOAD', log_context)
      print(download_info.value)
      print(download_info.value.url)
      pdf_url = download_info.value.url
      uploaded_pdf_url = upload_remote_warranty_pdf_to_s3(
        pdf_url, {'job_id': payload['job_id'], 'manufacturer_name': 'trane'})
      return uploaded_pdf_url, None

  return scrape(scraper)


def auto_address_input(page, address):
  street = address.get('street')
  unit = address.get('unit')
  city = address.get('city')
  state = address.get('state')
  zip = address.get('zip')

  address_to_fill = f"{street} {unit if unit else ''} {city} {state} {zip}"

  page.get_by_placeholder('Enter Address Line 1').click()
  page.get_by_placeholder('Enter Address Line 1').fill(address_to_fill)

  auto_address_dropdown = page.get_by_role('listbox')
  first_auto_address = auto_address_dropdown.locator(
    'li a').filter(has_not_text='#').first

  if first_auto_address.count() == 0:
    return False

  address_dropdown = page.get_by_role('listbox')
  address_dropdown.locator('li').locator(
    'a').filter(has_not_text='#').first.click()
  if unit:
    unit_selector = page.locator(
      "[model='contactData.equipmentAddress.address2'] >> visible=true")
    unit_selector.click()
    optionToSelect = unit_selector.locator('select').locator(
      'option', has_text=f"{unit}").text_content()
    unit_selector.locator('select').select_option(optionToSelect)

  return True


def manual_address_input(page, address):
  state = address.get('state')
  street = address.get('street')
  unit = address.get('unit')
  city = address.get('city')
  zip = address.get('zip')

  page.locator('#lState').select_option(state)
  page.get_by_placeholder('Enter Address Line 1').fill(street)
  if unit:
    page.get_by_placeholder('Enter Address Line 2 (Example').fill(unit)
  page.locator('#lCity').fill(city)
  page.locator('input[name="pZip"]').fill(zip)


def extra_fields_input(page, payload):
  owner_phone = payload.get('owner_phone')
  installer_phone = payload.get('installer_phone')
  owner_email = payload.get('owner_email')
  installer_email = payload.get('installer_email')
  installer_name = payload.get('installer_name')

  page.get_by_placeholder('Enter Phone Number').click()
  page.get_by_placeholder('Enter Phone Number').fill(
    owner_phone if owner_phone else installer_phone)

  page.get_by_placeholder('Enter Email').click()
  page.get_by_placeholder('Enter Email').fill(
    owner_email if owner_email else installer_email)

  page.get_by_placeholder('Enter Dealer / Builder Name').click()
  page.get_by_placeholder('Enter Dealer / Builder Name').fill(installer_name)

  page.get_by_placeholder('Enter Dealer / Builder Phone').click()
  page.get_by_placeholder(
    'Enter Dealer / Builder Phone').fill(installer_phone)

  page.get_by_placeholder('Enter Dealer / Builder Email').click()
  page.get_by_placeholder(
    'Enter Dealer / Builder Email').fill(installer_email)


def add_system(page, system_number):
  page.locator('#newSystem').click()
  page.get_by_role('heading', name='Add New System').click()
  page.get_by_placeholder('Enter system name').click()
  page.get_by_placeholder('Enter system name').fill(
    f"System{system_number}")
  page.get_by_role('button', name='Add').nth(1).click()
  page.locator(f"#systemRow-{system_number - 1}").click()


def add_equipment_item(page: Page, equipment_item):
  serial_number = equipment_item.get('serial_number')

  page.get_by_placeholder('Enter your serial number').click()
  page.get_by_placeholder('Enter your serial number').fill(serial_number)
  page.get_by_role("button", name="Add").click()

  time.sleep(5)

  error_message = page.locator('.overlay-content.popup10')
  if error_message.is_visible():
    is_already_registered = error_message.get_by_text(
      'This unit has already been registered').is_visible()
    if is_already_registered:
      error = f"Serial number previously registered: {serial_number}"
      print(error)
      return None, error

    is_already_associated = error_message.get_by_text(
      'is associated to another active registration').is_visible()
    if is_already_associated:
      error = f"Serial number previously associated: {serial_number}"
      print(error)
      return None, error

    is_serial_not_found = error_message.get_by_text(
      "(Serial Number Details not found)").first.is_visible()
    if is_serial_not_found:
      error = f"Serial number not found in database: {serial_number}"
      print(error)
      return None, error

  page.get_by_text('Install Date (MM/DD/YYYY):').first.click()
  page.get_by_role(
    'heading', name='Serialized Components', exact=True).click()
  page.get_by_role('textbox', name='MM/DD/YYYY').click()

  install_date = equipment_item.get('installed_on')
  page.get_by_role('textbox', name='MM/DD/YYYY').fill(install_date)
  page.get_by_role('button', name='Add').nth(1).click()
