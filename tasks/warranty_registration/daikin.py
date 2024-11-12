import time
from pathlib import Path
import urllib.parse

from celery_app import celery_app
from scrape import scrape


@celery_app.task
def register_daikin_warranty(payload):
  print(payload)

  def scraper(page):
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
      'owner_phone') != None and payload.get('owner_phone') != None else payload.get('installer_phone'))
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill(payload.get('owner_email') if payload.get(
      'owner_email') != None and payload.get('owner_email') != None else payload.get('installer_email'))
    page.get_by_label("Zip/Postal Code *").click()
    page.get_by_label(
      "Zip/Postal Code *").fill(payload.get('address').get("zip"))
    page.locator("reg-layout").click()
    page.get_by_role("textbox", name="Address1").click()
    page.get_by_role("textbox", name="Address1").fill(
      payload.get('address').get("street"))
    if payload.get('address').get("unit") != None and payload.get('address').get("unit") != None:
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

  scrape(scraper)
