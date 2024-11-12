import time
from pathlib import Path
import urllib.parse

from celery_app import celery_app
from scrape import scrape


@celery_app.task
def register_trane_warranty(payload):
  def scraper(page):
    download = None

    page.goto(
      'https://warrantyregistration.tranetechnologies.com/wrApp/index.html#/trane/welcome')
    # page.get_by_text('Commercial').click()
    # page.get_by_role('radio').nth(1).check()
    # page.get_by_role('radio').first.check()
    # page.pause()
    if payload.get('type') == 'Residential':
      page.get_by_role('radio').first.check()
    elif payload.get('type') == 'Commercial':
      page.get_by_role('radio').nth(1).check()
    else:
      error = ('Unknown customer type')
      print('Unknown customer type')
      return error
    # page.get_by_text('Commercial').click()
    # page.get_by_text('Residential Commercial').click()
    # page.get_by_role('radio').nth(1).check()
    # page.get_by_role('radio').first.check()
    if payload.get('address').get('unit') != None and payload.get('address').get('unit'):
      unit = payload.get('address').get('unit')
    else:
      unit = ''

    page.get_by_placeholder('Enter First Name').click()
    page.get_by_placeholder('Enter First Name').fill(payload.get('first_name'))
    page.get_by_placeholder('Enter Last Name').click()
    page.get_by_placeholder('Enter Last Name').fill(payload.get('last_name'))
    page.get_by_placeholder('Enter Address Line 1').click()
    page.get_by_placeholder('Enter Address Line 1').fill(
      f"{payload.get('address').get('street')} {(payload.get('address').get('unit')) if (payload.get('address').get('unit')) != None else ''} {payload.get('address').get('city')} {payload.get('address').get('state')} {payload.get('address').get('zip')}")
    # page.pause()
    try:
      time.sleep(2)
      page.pause()
      address_dropdown = page.get_by_role('listbox')
      # address_dropdown.locator('li').locator('a').nth(1).click()
      address_dropdown.locator('li').locator(
        'a').filter(has_not_text='#').first.click()
      if payload.get('address').get('unit') != None and payload.get('address').get('unit'):
        page.pause()
        # unit_selector = page.get_by_placeholder('Select Unit')
        unit_selector = page.locator(
          "[model='contactData.equipmentAddress.address2'] >> visible=true")
        unit_selector.click()
        print(unit_selector)
        optionToSelect = unit_selector.locator('select').locator(
          'option', has_text=f"{payload.get('address').get('unit')}").text_content()
        print(optionToSelect)
        unit_selector.locator('select').select_option(optionToSelect)
        # page.pause()
    except Exception as e:
      print('could not verify address with google')
      page.pause()
      try:
        page.get_by_placeholder('Enter Address Line 1').fill(
          payload.get('address').get('street'))
        if payload.get('address').get('unit') != None and payload.get('address').get('unit'):
          page.get_by_placeholder('Enter Address Line 2 (Example').fill(
            payload.get('address').get('unit'))
        page.locator('#lCity').fill(payload.get('address').get('city'))
        page.locator('#lState').select_option(
          payload.get('address').get('state'))
        page.locator('input[name="pZip"]').fill(
          payload.get('address').get('zip'))
      except Exception as e:
        print('could not verify address manually')
        error = 'could not verify address manually'
        return error
    # address_dropdown.select_option(index=0)

    # # page.get_by_role('option', name=f"{payload.get('address').get('street')} {(payload.get('address').get('unit')) if (payload.get('address').get('unit')) != None else ''} {payload.get('address').get('city')} {payload.get('address').get('state')} {payload.get('address').get('zip')}").click()
    # page.pause()

    #  page.get_by_placeholder('Enter Address Line 2').click()
    #  page.get_by_placeholder('Enter Address Line 2').fill(f"{payload.get('address').get('unit')}")
    page.get_by_placeholder('Enter Phone Number').click()
    page.get_by_placeholder('Enter Phone Number').fill(payload.get(
      'owner_phone') if payload.get('owner_phone') != None else payload.get('installer_phone'))
    # page.pause()
    page.get_by_placeholder('Enter Email').click()
    page.get_by_placeholder('Enter Email').fill(payload.get('owner_email') if payload.get(
      'owner_email') != None else payload.get('installer_email'))
    # page.pause()
    page.get_by_placeholder('Enter Dealer / Builder Name').click()
    page.get_by_placeholder(
      'Enter Dealer / Builder Name').fill(payload.get('installer_name'))
    # page.pause()
    page.get_by_placeholder('Enter Dealer / Builder Phone').click()
    page.get_by_placeholder(
      'Enter Dealer / Builder Phone').fill(payload.get('installer_phone'))
    # page.pause()
    page.get_by_placeholder('Enter Dealer / Builder Email').click()
    page.get_by_placeholder(
      'Enter Dealer / Builder Email').fill(payload.get('installer_email'))
    # page.pause()
    page.get_by_role('button', name='Continue').click(timeout=2000)

    if page.get_by_text('Verify your Home owner/').is_visible():
      page.get_by_text('Verify your Home owner/').click()
      page.get_by_role('button', name='Continue').click()

    # page.pause()
    page.locator('div').filter(
      has_text='Components Components Search').nth(1).click()
    # page.pause()
    time.sleep(2)
    equipments = payload.get('equipment')
    systems = payload.get('equipment')
    system_number = 1
    for system in systems:
      equipments = system.get('equipment')
      page.pause()
      if system_number > 1:
        # page.pause()
        page.locator('#newSystem').click()
        page.get_by_role('heading', name='Add New System').click()
        page.get_by_placeholder('Enter system name').click()
        page.get_by_placeholder('Enter system name').fill(
          f"System{system_number}")
        page.get_by_role('button', name='Add').nth(1).click()
        page.locator(f"#systemRow-{system_number-1}").click()
        # page.get_by_text(f"System{system_number} Click to edit system").click(force=True)
      for equipment in equipments:
        # page.pause()
        page.get_by_placeholder('Enter your serial number').click()
        page.get_by_placeholder('Enter your serial number').fill(
          equipment.get('serial_number'))
        # Check to see if unit is registered
        try:
          page.get_by_text(
            'This unit has already been registered').click(timeout=2000)
          page.get_by_text(
            'is associated to another active registration.').click(timeout=2000)
          error = (
            f"Serial number previously registered: {equipment.get('serial_number')}")
          print(
            f"Serial number previously registered: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print('serial number not registered')
        page.get_by_role('button', name='Add').click()
        # Check to see if unit is eligible
        try:
          page.get_by_text(
            'Serial Number not eligible').first.click(timeout=2000)
          error = (
            f"Serial number not eligible for registration: {equipment.get('serial_number')}")
          print(
            f"Serial number not eligible for registration: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print('serial number is eligible')
        # Check to see if unit serial is correct
        try:
          page.get_by_text(
            '(Error during serial number').first.click(timeout=2000)
          error = (
            f"Error with serial number: {equipment.get('serial_number')}")
          print(f"Error with serial number: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print('serial number is correct')
        page.pause()
        try:
          page.get_by_text('Component validation failed').click(timeout=2000)
          error = (
            f"Error with serial number: {equipment.get('serial_number')}")
          print(f"Error with serial number: {equipment.get('serial_number')}")
          return error
        except Exception as e:
          print('serial number is correct')
        page.get_by_text('Install Date (MM/DD/YYYY):').first.click()
        page.get_by_role(
          'heading', name='Serialized Components', exact=True).click()
        page.get_by_role('textbox', name='MM/DD/YYYY').click()
        page.get_by_role(
          'textbox', name='MM/DD/YYYY').fill(payload.get('install_date'))
        # page.pause()
        page.get_by_role('button', name='Add').nth(1).click()

        # page.pause()
        components_table = page.locator('#componentTable')
        print(components_table)
        # page.pause()
        serial_number_found = components_table.get_by_text(
          f"{equipment.get('serial_number')}")
        print(serial_number_found.text_content())
      system_number += 1
    # page.pause()
    page.get_by_role('button', name='Continue').click()
    # page.pause()
    page.get_by_role('button', name='Complete Registration').click()
    # page.pause()
    time.sleep(5)
    with page.expect_download() as download_info:
      page.get_by_role('button', name='View Warranty Certificate').click()
    download = download_info.value
    # page.pause()
    # page.emulate_media(media='screen')
    file_name = urllib.parse.quote(
      f"trane_warranty_{payload.get('first_name')}_{payload.get('last_name')}_{payload.get('st_job_id')}.pdf").lower()
    print('saving download')
    download.save_as(Path.home().joinpath('Downloads', file_name))
    # pdf = page.pdf(path=file_name)
    # pdf.save_as(Path.home().joinpath('Downloads', file_name))
    # print(file_name)
    # print('saving download')
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
    #   with open(pdf.name, 'rb') as pdf:
    #     encoded_pdf = base64.b64encode(pdf.read())
    #   r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/warranty_upload', data={'st_jobs_id': payload.get('st_job_id') , 'companies_id': payload.get('companies_id'), 'manufacturer': 'Trane', 'warranty': encoded_pdf, 'needs_review': False, 'warranty_review_reason': None}, timeout=30)
    #   print(r)

    # with page.expect_download() as download_info:
    #     with page.expect_popup() as page1_info:
    #         page.get_by_role('button', name='View Warranty Certificate').click()
    #     page1 = page1_info.value
    # download = download_info.value
    # ---------------------

  scrape(scraper)
