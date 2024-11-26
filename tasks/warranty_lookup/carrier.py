import time
import base64
import img2pdf
import json
import requests
from playwright.sync_api import Page

from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from tempfile import NamedTemporaryFile

from celery_app import celery_app
from scrape import scrape

load_dotenv()


@celery_app.task
def get_carrier_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  print(f"### Starting Carrier Warranty Lookup: {serial_number}")

  def scraper(page: Page):
    html = None
    pdf = None
    page.goto(
        f"https://www.carrierenterprise.com/warranty/{serial_number}")
    try:
      # print(page.get_by_role("heading", name="Select Model"))
      page.get_by_role("heading", name="Select Model").click()
      # print(page.locator(".main-page-2b_").get_by_role("list").get_by_role("link").all())
      page.locator(
          ".main-page-2b_").get_by_role("list").get_by_role("link").nth(0).click()

      # "main-page-2b_
      # print(page.locator('[href*="/warranty/"]'))
      # page.locator('[href*="/warranty/"]').click()
      # # first_link[0].click()
    except Exception as e:
      print(f"something went wrong: {e}")
    try:
      page.get_by_text('Entitlement Overview').click()
      html = page.query_selector(".main-page-2b_").inner_html()
    except Exception as e:
      print(f"something went wrong: {e}")
    try:
      try:
        page.get_by_role('button', name='Accept All Cookies').click()
      except Exception as e:
        print(f"something went wrong: {e}")
      try:
        link = page.get_by_role('link', name='Back To Models')
        link.evaluate("(el) => el.style.display = 'none'")
      except Exception as e:
        print(f"something went wrong: {e}")

      try:
        button = page.get_by_role('link', name='View Parts')
        button.evaluate("(el) => el.style.display = 'none'")
      except Exception as e:
        print(f"something went wrong: {e}")

      text = page.query_selector(".lead-root-3bJ ")
      text.evaluate("(el) => el.style.display = 'none'")
      form = page.locator(".main-page-2b_").locator("form")
      form.evaluate("(el) => el.style.display = 'none'")

      rows = page.query_selector_all("tr")
      for row in rows:
        row.evaluate("(el) => el.style.background = '#fff9db'")
      page.get_by_role("heading", name="Warranty", exact=True).click()

      time.sleep(5)

      try:
        page.get_by_text('Entitlement Overview').click()
        img_temp_file = NamedTemporaryFile(delete=True)
        pdf_temp_file = NamedTemporaryFile(delete=True)
        page.query_selector(
            ".wrapPanel-root-3px").screenshot(path=img_temp_file.name)
        image = Image.open(img_temp_file.name)
        pdf_bytes = img2pdf.convert(image.filename)
        pdf = open(pdf_temp_file.name, "wb")
        pdf.write(pdf_bytes)
        pdf.close()
        img_temp_file.flush()
        pdf_temp_file.flush()

        return html, pdf_temp_file
      except Exception as e:
        print(f"something went wrong: {e}")

    except Exception as e:
      print(f"something went wrong: {e}")
    # print(html)

    return html, pdf

  html, pdf = scrape(scraper)

# start bs4 scrape
  # return html
  if html and html is not (None):
    # print(html)
    soup = BeautifulSoup(html, "html.parser")

    if soup.select_one('h2:-soup-contains("Serial Number")'):

      warranty_object = {}
      warranty_object["is_registered"] = False
      warranty_object["shipped_date"] = None
      warranty_object["install_date"] = None
      warranty_object["register_date"] = None
      warranty_object["manufacture_date"] = None
      warranty_object["last_name_match"] = False
      warranty_object["certificate"] = None

      # GET MODEL NUMBER

      model_number = soup.select_one(
          'th:-soup-contains("Discrete Model Number")').find_next('td')
      model_number = model_number.get_text().strip()
      if model_number:
        warranty_object["model_number"] = model_number
      else:
        model_number = soup.select_one(
            'th:-soup-contains("Model Number")').find_next('td').find_next('span')
        warranty_object["model_number"] = model_number.get_text(
        ).strip()

      # GET OWNER NAME
      owner_name = soup.select_one(
          'th:-soup-contains("Owner")').find_next('td')
      owner_name = owner_name.get_text().strip()
      if owner_name and owner_name is not (None):
        if owner_name.split()[1] == owner_last_name:
          warranty_object["last_name_match"] = True

      # GET INSTALL DATE
      install_date = soup.select_one(
          'th:-soup-contains("Date Installed")').find_next('td')
      install_date = install_date.get_text().strip()
      if install_date and install_date is not (None):
        # 2022-11-03
        install_date = time.mktime(datetime.strptime(
            install_date, "%Y-%m-%d").timetuple())
        warranty_object["install_date"] = int(install_date)

      # GET SHIPPED DATE
      shipped_date = soup.select_one(
          'th:-soup-contains("Shipped Date")').find_next('td')
      shipped_date = shipped_date.get_text().strip()
      if shipped_date and shipped_date is not (None):
        # 2022-11-03
        shipped_date = time.mktime(datetime.strptime(
            shipped_date, "%Y-%m-%d").timetuple())
        warranty_object["shipped_date"] = int(shipped_date)

      # print(warranty_object)

      # GET INDIVIDUAL WARRANTIES
      warranties = None
      if soup.select_one('h2:-soup-contains("Warranty Info (Original)")'):
        warranties = []
        warranty_table = soup.select_one(
            'h2:-soup-contains("Warranty Info (Original)")').find_next('table')

        warranty_body = warranty_table.find("tbody")
        # print(warranty_body)
        rows = warranty_body.findAll('tr')
        # print(rows)
        if soup.select_one('th:-soup-contains("Warranty Start")'):
          # print("registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            # print(cols)
            # unwanted = cols[0].find('a')
            # unwanted.extract()
            warranty_details["name"] = cols[0].get_text().strip()
            # print(warranty_details)
            warranty_details["description"] = cols[1].get_text(
            ).strip()
            start_date = cols[3].get_text().strip()
            # 2022-11-03
            start_date = time.mktime(datetime.strptime(
                start_date, "%Y-%m-%d").timetuple())
            warranty_details["start_date"] = int(start_date)
            end_date = cols[4].get_text().strip()
            # 2022-11-03
            end_date = time.mktime(datetime.strptime(
                end_date, "%Y-%m-%d").timetuple())
            warranty_details["end_date"] = int(end_date)

            if "enhance" in cols[0].get_text().strip().lower():
              warranty_details["type"] = "Extended"
            else:
              warranty_details["type"] = "Standard"
            warranties.append(warranty_details)

          warranty_object["warranties"] = warranties

          if len(warranties) > 0:
            warranty_object["is_registered"] = True

          print(warranty_object)
        else:
          # print("no registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            warranty_details["name"] = cols[0].get_text().strip()
            warranty_details["description"] = cols[1].get_text(
            ).strip()
            warranty_details["type"] = "Standard"
            warranties.append(warranty_details)
          warranty_object["warranties"] = warranties
      elif soup.select_one('h2:-soup-contains("Warranty Info (All)")'):
        warranties = []
        warranty_table = soup.select_one(
            'h2:-soup-contains("Warranty Info (All)")').find_next('table')

        warranty_body = warranty_table.find("tbody")
        # print(warranty_body)
        rows = warranty_body.findAll('tr')
        # print(rows)
        if soup.select_one('th:-soup-contains("Warranty Start")'):
          # print("registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            # print(cols)
            # unwanted = cols[0].find('a')
            # unwanted.extract()
            warranty_details["name"] = cols[0].get_text().strip()
            # print(warranty_details)
            warranty_details["description"] = cols[1].get_text(
            ).strip()
            start_date = cols[3].get_text().strip()
            # 2022-11-03
            start_date = time.mktime(datetime.strptime(
                start_date, "%Y-%m-%d").timetuple())
            warranty_details["start_date"] = int(start_date)
            end_date = cols[4].get_text().strip()
            # 2022-11-03
            end_date = time.mktime(datetime.strptime(
                end_date, "%Y-%m-%d").timetuple())
            warranty_details["end_date"] = int(end_date)

            if "enhance" in cols[0].get_text().strip().lower():
              warranty_details["type"] = "Extended"
            else:
              warranty_details["type"] = "Standard"
            warranties.append(warranty_details)

          warranty_object["warranties"] = warranties

          if len(warranties) > 0:
            warranty_object["is_registered"] = True

          print(warranty_object)
        else:
          # print("no registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            warranty_details["name"] = cols[0].get_text().strip()
            warranty_details["description"] = cols[1].get_text(
            ).strip()
            warranty_details["type"] = "Standard"
            warranties.append(warranty_details)
          warranty_object["warranties"] = warranties

    else:
      warranty_object = None
  else:
    warranty_object = None

  # pdf = None
  print(warranty_object)
  encoded_pdf = None
  if pdf is not None:
    with open(pdf.name, "rb") as pdf:
      encoded_pdf = base64.b64encode(pdf.read()).decode('ascii')

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)
