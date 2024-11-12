import time
import base64
import io
import json
import os
import pdfplumber
import re
import redis
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from langchain.chains import create_extraction_chain_pydantic
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from typing import Sequence

from celery_app import celery_app
from constants import LENNOX_AUTH_CODE_KEY
from scrape import scrape_with_context

load_dotenv()

redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL'), db=0)


# GET LENNOX WARRANTY
@celery_app.task
def get_lennox_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  pdf_base64 = None

  print(f"### Starting Lennox Warranty Lookup: {serial_number}")

  load_dotenv()
  LENNOX_EMAIL = os.getenv("LENNOX_EMAIL")
  LENNOX_PASSWORD = os.getenv("LENNOX_PASSWORD")

  from playwright.sync_api import Playwright, sync_playwright

  def try_2fa(page):
    redis_client.delete(LENNOX_AUTH_CODE_KEY)

    url = page.url
    if url == 'https://www.lennoxpros.com/':
      return

    print('starting 2FA flow...')
    page.check('#mfa_email')
    page.click('button:has-text("Send Code")')

    code = poll_for_code()
    print('code:', code)
    page.get_by_role("textbox", name="Verification Code").click()
    page.get_by_role("textbox", name="Verification Code").fill(code)
    page.get_by_role("button", name="Verify Code").click()

  POLL_TRIES_SECONDS = 120

  def poll_for_code():
    for _ in range(POLL_TRIES_SECONDS):
      time.sleep(1)
      code_bytes = redis_client.get(LENNOX_AUTH_CODE_KEY)
      if code_bytes:
        break

    redis_client.delete(LENNOX_AUTH_CODE_KEY)
    return code_bytes.decode('ascii')

  def lennox_login(page):
    page.goto(
        'https://www.lennoxpros.com/samlsinglesignon/saml/?idp=B2C_1A_signup_signin_SAML')
    page.fill('input[placeholder="Email Address"]', LENNOX_EMAIL)
    page.fill('input[placeholder="Password"]', LENNOX_PASSWORD)
    page.get_by_role("button", name="Sign In").click()
    print('login clicked...')
    page.wait_for_event('domcontentloaded')
    print('post-login page:', page.url)
    try_2fa(page)
    print('passed try2FA', page.url)

  def scraper(page, **kwargs) -> None:
    text = None
    html = None
    pdf_base64 = None
    kwargs.get('context').add_cookies([{
        'name': 'lennoxUserRegion',
        'value': 'US',
        'domain': '.lennoxpros.com',
        'path': '/'
    }])

    lennox_login(page)

    page.get_by_role("link", name="Warranty").first.click()
    page.get_by_role(
        "link", name="Warranty Registration Certificate Lookup").click()
    print("starting to fill form")
    page.get_by_label("Equipment Owner Last Name*").click()
    page.get_by_label("Equipment Owner Last Name*").fill(owner_last_name)
    page.get_by_label("Serial Number or Registration Number*").click()
    page.get_by_label(
        "Serial Number or Registration Number*").fill(serial_number)
    page.get_by_role("button", name="Search").click()
    print(owner_last_name)
    print(serial_number)
    print("searching for serial number")
    try:
      page.locator("#warrantyLookUpTable").click()
      print("found lookup table")
      pdf_base64 = page.get_by_role(
          "link", name="Print").get_attribute('data-stream')
    except Exception as e:
      print(f"something went wrong: {e}")
      try:
        print("trying quick coverage tool")
        page.get_by_role(
            "link", name="Quick Coverage Lookup Tool").click()
        page.get_by_role("button", name="I Agree").click()
        page.get_by_label("Residential").check()
        page.locator("#txtSearchSerialNum").click()
        page.locator("#txtSearchSerialNum").fill(serial_number)
        page.get_by_role("button", name="Search").click()
        page.locator("#PanelLennoxOutput").click()
        html = page.locator("#PanelLennoxOutput").inner_html()
        print(html)
      except Exception as e:
        print(f"something went wrong: {e}")

    texts = ""
    if pdf_base64 is not (None):
      pdf_bytes = base64.b64decode(pdf_base64)
      pdf_file = io.BytesIO(pdf_bytes)
      reader = pdfplumber.open(pdf_file)
      # reader = PdfReader(pdf)
      texts = ""
      for page in reader.pages:
        text = page.extract_text()
        texts += text
      return {"text": texts, "pdf_base64": pdf_base64, "html": None}
    elif html is not (None):
      return {"text": None, "pdf_base64": None, "html": html}
    else:
      return None

  text = None
  html = None

  result = scrape_with_context(scraper)
  if result is not (None):
    text = result["text"]
    html = result["html"]
    pdf_base64 = result["pdf_base64"]

  if result is not (None):
    if html is not (None):
      soup = BeautifulSoup(html, "html.parser")

      warranty_object = {}
      warranty_object["is_registered"] = False
      warranty_object["shipped_date"] = None
      warranty_object["install_date"] = None
      warranty_object["register_date"] = None
      warranty_object["manufacture_date"] = None
      warranty_object["model_number"] = None
      warranty_object["shipped_date"] = None
      warranty_object["last_name_match"] = False
      warranty_object["certificate"] = None
      warranties = None

      # GET MODEL NUMBER
      model_number = soup.select_one("#lblModelNumber")
      warranty_object["model_number"] = model_number.get_text().strip()

      # GET INSTALL DATE
      install_date = soup.select_one("#lblInsDate")
      install_date = install_date.get_text().strip()
      if install_date and install_date is not (None) and "Not Available" not in install_date:
        # 09/13/2023
        install_date = time.mktime(datetime.strptime(
            install_date, "%m/%d/%Y").timetuple())
        warranty_object["install_date"] = int(install_date)
        warranty_object["is_registered"] = True
      else:
        install_date = None

      # GET WARRANTIES

      # GET STANDARD PARTS WARRANTY
      standard_parts_warranty_term = soup.select_one(
          "#lblStandardWarranty").get_text().strip()
      if "Not Available" not in str(standard_parts_warranty_term) and install_date:

        warranties = []
        warranty = {}

        warranty["start_date"] = int(install_date)

        term = standard_parts_warranty_term
        years = re.search(r"\d+", term).group()
        # print(int(years))
        years = int(years)
        # print(int(end_date))
        end_date = (datetime.fromtimestamp(install_date) +
                    relativedelta(years=years)).strftime("%m/%d/%Y")
        # 2021-04-01T00:00:00
        end_date = time.mktime(datetime.strptime(
            end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)
        warranty["name"] = "Parts"
        warranty["type"] = "Standard"
        warranties.append(warranty)
      elif "Not Available" not in str(standard_parts_warranty_term):
        warranties = []
        warranty = {}
        warranty["name"] = "Parts"
        warranty["type"] = "Standard"
        warranty["description"] = standard_parts_warranty_term
        warranties.append(warranty)

      # GET EXTENDED PARTS WARRANTY
      extended_parts_warranty_end_date = soup.select_one(
          "#lblWarrantyExpiration").get_text().strip()
      if "Not Available" not in str(extended_parts_warranty_end_date) and install_date:
        warranty = {}

        warranty["start_date"] = int(install_date)

        end_date = extended_parts_warranty_end_date
        end_date = time.mktime(datetime.strptime(
            end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)
        warranty["name"] = "Parts"
        warranty["type"] = "Extended"
        warranties.append(warranty)

      # GET STANDARD LABORY WARRANTY
      standard_labor_warranty_end_date = soup.select_one(
          "#lblStandardLaborExpiration").get_text().strip()
      if "Not Available" not in str(standard_labor_warranty_end_date) and install_date:

        warranty = {}

        warranty["start_date"] = int(install_date)

        end_date = standard_labor_warranty_end_date
        end_date = time.mktime(datetime.strptime(
            end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)
        warranty["name"] = "Labor"
        warranty["type"] = "Standard"
        warranties.append(warranty)

      warranty_object["warranties"] = warranties

    if text is not (None):

      # # Pydantic data class
      # class Properties(BaseModel):
      #   model_number: str
      #   serial_number: str
      #   part: str
      #   parts_warranty_expiration: str
      #   installation_date: str
      #   lennox_labor_expiration: str

      # parser = PydanticOutputParser(pydantic_object=Properties)

      warranty_search_prompt = PromptTemplate(
          input_variables=["text"],
          template='''Using the input given below list all of the warranties for each unique serial number with the following information:
            
            - serial number or serial #
            - part (examples: "functional parts", "parts", "compressor", "tank", "heat exchanger", "coil", "furnace", "air conditioner")
            - model number or model #
            - installation date
            - parts warranty expiration
            - lennox labor expiration

            input: {text}
            ''',
          # partial_variables={"format_instructions": parser.get_format_instructions()}
      )

      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = LLMChain(llm=llm, prompt=warranty_search_prompt)
      output = chain.run({
          'text': text
      })
      print(output)

      # ### Set schema to structure internet search data in JSON
      # schema = {
      #   "properties": {
      #     "model_number": {"type": "string"},
      #     "serial_number": {"type": "string"},
      #     "part": {"type": "string"},
      #     "parts_warranty_expiration": {"type": "string"},
      #     "installation_date": {"type": "string"},
      #     "lennox_labor_expiration": {"type": "string"},
      #   },
      #     "required": ["model_number", "serial_number", "part", "parts_warranty_expiration", "installation_date", "lennox_labor_expiration"],
      # }

      # ### Build chain to structure raw text from trane pdf
      # llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      # chain = create_extraction_chain(schema, llm)
      # messages = [{"role": "user", "content": output}]
      # lennox_warranty = chain.run(messages)

      # output = '''
      #   - Serial Number: 5921B14178
      #   - Part: Furnace
      #   - Model Number: SL280UH090V36B-04
      #   - Installation Date: 4/28/2021
      # '''

      # Pydantic data class
      class Property(BaseModel):
        model_number: str
        serial_number: str
        part: str
        parts_warranty_expiration: str
        installation_date: str
        lennox_labor_expiration: str

      class Properties(BaseModel):
        property: Sequence[Property]

      parser = PydanticOutputParser(pydantic_object=Properties)
      # Build chain to structure raw text from trane pdf
      print("starting pydantic")
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      try:
        chain = create_extraction_chain_pydantic(
            pydantic_schema=Property, llm=llm)
        lennox_warranty = chain.run(output)
        print(lennox_warranty)
      except Exception as e:
        print(f"something went wrong {e}")
        print("trying new parse")
        try:
          chain = create_extraction_chain_pydantic(
              pydantic_schema=Properties, llm=llm)
          lennox_warranty = chain.run(output)
          lennox_warranty = lennox_warranty[0].property
          print(lennox_warranty)
        except Exception as e:
          print(f"something went wrong {e}")

      lennox_warranty = json.dumps(
          [warranty.__dict__ for warranty in lennox_warranty])
      # lennox_warranty = json.dumps(lennox_warranty.__dict__)
      print(lennox_warranty)

      lennox_warranty = json.loads(lennox_warranty)
      # print(lennox_warranty)

      if lennox_warranty:
        warranty_object = {}
        warranty_object["is_registered"] = True
        warranty_object["shipped_date"] = None
        warranty_object["install_date"] = None
        warranty_object["register_date"] = None
        warranty_object["manufacture_date"] = None
        warranty_object["model_number"] = None
        warranty_object["shipped_date"] = None
        warranty_object["last_name_match"] = True
        warranty_object["certificate"] = None
        # print(html)

        # print("here first")
        warranties = [
            obj for obj in lennox_warranty if obj['serial_number'] == serial_number]
        for warranty in warranties:
          # 06/22/2014
          end_date = warranty["parts_warranty_expiration"]
          end_date = time.mktime(datetime.strptime(
              end_date, "%m/%d/%Y").timetuple())
          warranty["end_date"] = int(end_date)

          # 06/22/2014
          start_date = warranty["installation_date"]
          start_date = time.mktime(datetime.strptime(
              start_date, "%m/%d/%Y").timetuple())
          warranty["start_date"] = int(start_date)

          warranty_object["install_date"] = int(start_date)
          warranty_object["register_date"] = int(start_date)
          warranty_object["model_number"] = warranty["model_number"]
          warranty["name"] = warranty["part"].title() + " Parts"

          # Check for labor warranty
          labor_warranty_exists = warranty["lennox_labor_expiration"]
          print(f"labor warranty: {labor_warranty_exists}")
          if "N/A" not in str(labor_warranty_exists):
            labor_warranty = {}
          # if labor_warranty is not("N/A"):
            print("creating labor warranty")
            # 06/22/2014
            end_date = warranty["labor_expiration"]
            end_date = time.mktime(datetime.strptime(
                end_date, "%m/%d/%Y").timetuple())
            labor_warranty["end_date"] = int(end_date)
            labor_warranty["start_date"] = int(start_date)
            labor_warranty["name"] = "Labor"
            warranties.append(labor_warranty)
            print(labor_warranty)

          del warranty["model_number"]
          del warranty["serial_number"]
          del warranty["parts_warranty_expiration"]
          del warranty["installation_date"]
          del warranty["lennox_labor_expiration"]
          del warranty["part"]

          # delattr(warranty, "parts")
          # delattr(warranty, "term")

        warranty_object["warranties"] = warranties
      else:
        warranty_object = None

      # print(f'''ALL Warranties:
      #       {trane_warranty}''')
      # print(f'''RELEVANT Warranties:
      #       {relevant_warranty}''')
  else:
    warranty_object = None

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": pdf_base64}

  else:
    if equipment_scan_id and equipment_scan_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": pdf_base64}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not (None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                        "warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": pdf_base64}, timeout=30)
      print(r)
