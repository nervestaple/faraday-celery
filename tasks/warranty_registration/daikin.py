import time
from pathlib import Path
from typing import Union
import urllib.parse
from playwright.sync_api import Page

from s3 import upload_local_warranty_pdf_to_s3
from scrape import scrape


def register_daikin_warranty(payload, systems) -> tuple[Union[str, None], Union[str, None]]:

  def scraper(page: Page) -> tuple[Union[str, None], Union[str, None]]:
    page.goto("https://warranty.goodmanmfg.com/newregistration/")

    for system_equipment in systems:
      for equipment in system_equipment:
        page.get_by_role("textbox", name="Serial number").click(timeout=2000)
        page.get_by_role("textbox", name="Serial number").fill(
          equipment.get('serial_number'))
        page.get_by_text("1Product Info2Customer").click()

        try:
          page.get_by_text(
            "This unit has already been registered").click(timeout=2000)
          error = (
            f"Serial number previously registered: {equipment.get('serial_number')}")
          print(
            f"Serial number previously registered: {equipment.get('serial_number')}")
          return None, error
        except Exception as e:
          print("serial number not registered")

        try:
          page.get_by_role(
            "cell", name=f"{equipment.get('serial_number')}").click(timeout=10000)
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
            return None, error

    page.locator("[formcontrolname='installDate'] >> visible=true").fill(
      payload.get('install_date'))
    # print('here')

    if payload.get('type') == "Residential":
      page.get_by_text("Residential(Owner Occupied").click()
    elif payload.get('type') == "Commercial":
      page.get_by_text("Commercial").click()
    else:
      error = ("Unknown customer type")
      print("Unknown customer type")
      return None, error
    # page.locator("#mat-radio-6 > .mat-radio-label > .mat-radio-container").click()

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

    page.get_by_role("button", name="Next").click()

    try:
      page.get_by_role("cell", name="Recommended Address").click(timeout=2000)
      page.get_by_role("button", name="Use address recommended").click()
    except Exception as e:
      print("did not verify address")

    page.get_by_role("textbox", name="Dealer/Builder*").click()
    page.get_by_role(
      "textbox", name="Dealer/Builder*").fill(payload.get('installer_name'))
    page.get_by_role("textbox", name="Dealer/Builder Phone*").click()
    page.get_by_role(
      "textbox", name="Dealer/Builder Phone*").fill(payload.get('installer_phone'))

    page.pause()
    print(
      f"BEFORE COMPLETING DAIKIN REGISTRATION, job_id: {payload['job_id']}")
    page.get_by_role("button", name="Register").click()
    try:
      page.get_by_text("Please confirm the name/").click(timeout=2000)
      page.get_by_role("button", name="Yes").click()
    except Exception as e:
      print("no dialog to confirm address after registration")
    try:
      page.get_by_text("Congratulations! This product").click(timeout=2000)

      page.get_by_role("button", name="Affirm", exact=True).click(force=True)
      page.get_by_text("Please confirm the name/").click(force=True)
      page.get_by_role("button", name="Yes").click(force=True)
    except Exception as e:
      print(f"something went wrong: {e}")

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

    time.sleep(2)
    print(f"AFTER COMPLETING DAIKIN REGISTRATION, job_id: {payload['job_id']}")
    page.pause()
    with page.expect_download() as download_info:
      page.get_by_role("button", name="Download Certificate").click(
        force=True, timeout=2000)

      local_path = download_info.value.path()
      uploaded_pdf_path = upload_local_warranty_pdf_to_s3(
        local_path, {'job_id': payload['job_id'], 'manufacturer_name': 'daikin'})
      return uploaded_pdf_path, None

  return scrape(scraper)
