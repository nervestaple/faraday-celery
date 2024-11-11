import time
import base64
import json
import os
import pdfplumber
import re
import requests

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from langchain.chains import create_extraction_chain_pydantic
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from tempfile import NamedTemporaryFile

from celery_app import celery_app

load_dotenv()


@celery_app.task
def get_trane_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):

  print(f"### Starting Trane Warranty Lookup: {serial_number}")

  load_dotenv()

  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
    text = None
    download = None
    is_dev = os.getenv('ENVIRONMENT') == 'development'
    browser = playwright.chromium.launch(
        headless=(not is_dev), slow_mo=50 if is_dev else 0)
    context = browser.new_context()
    page = context.new_page()
    page.goto(
        "https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
    time.sleep(5)
    page.locator("input[name=\"serialNo\"]").click()
    page.locator("input[name=\"serialNo\"]").fill(serial_number)
    try:
      page.locator("input[name=\"lastName\"]").click()
      page.locator("input[name=\"lastName\"]").fill(owner_last_name)
    except Exception as e:
      print(f"something went wrong: {e}")
    page.get_by_role("button", name="Search").click()
    time.sleep(5)
    try:
      with page.expect_download() as download_info:
        page.get_by_role("button", name="Search").click()
      download = download_info.value
    except Exception as e:
      print(f"something went wrong: {e}")
      is_dev = os.getenv('ENVIRONMENT') == 'development'
      browser = playwright.chromium.launch(
          headless=(not is_dev), slow_mo=50 if is_dev else 0)
      context = browser.new_context()
      page = context.new_page()
      page.goto(
          "https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
      time.sleep(5)
      page.locator("input[name=\"serialNo\"]").click()
      page.locator("input[name=\"serialNo\"]").fill(serial_number)
      page.get_by_role("button", name="Search").click()
      time.sleep(5)
      try:
        with page.expect_download() as download_info:
          page.get_by_role("button", name="Search").click()
        download = download_info.value
      except Exception as e:
        print(f"something went wrong: {e}")

    texts = ""
    if download is not None:
      temp_file = NamedTemporaryFile(delete=True)
      download.save_as(temp_file.name)
      temp_file.flush()

      # pdf = pdfplumber.open(pdf)
      reader = pdfplumber.open(temp_file)
      # reader = PdfReader(pdf)
      texts = ""
      for page in reader.pages:
        text = page.extract_text()
        texts += text
      context.close()
      browser.close()
      return {"text": texts, "pdf": temp_file}

    context.close()
    browser.close()
    return None

  html = None
  pdf = None
  with sync_playwright() as playwright:
    result = run(playwright)
    if result is not None:
      print(result)
      html = result["text"]
      pdf = result["pdf"]

  if result is not (None):

    warranty_search_prompt = PromptTemplate(
        input_variables=["html"],
        template='''Using the input given below list all of the warranties for each serial number and term end date with the following information:
            
          warranty number of warranty#
          serial number or serial#
          part (examples: "functional parts", "parts", "compressor", "tank", "heat exchanger")
          equipment type (examples: "Air Conditioner", "Furnace", "Coil", "Thermostat", "Package")
          system number
          model number or model#
          end date
          term

          input: {html}
          '''
    )

    llm = AzureChatOpenAI(deployment_name="gpt35turbo",
                          model_name="gpt-35-turbo", temperature=0)
    chain = LLMChain(llm=llm, prompt=warranty_search_prompt)
    output = chain.run({
        'html': html
    })
    print(output)

    # ### Set schema to structure internet search data in JSON
    # schema = {
    #   "properties": {
    #     "model_number": {"type": "string"},
    #     "serial_number": {"type": "string"},
    #     "part": {"type": "string"},
    #     "end_date": {"type": "string"},
    #     "term": {"type": "string"},
    #   },
    #     "required": ["model_number", "serial_number", "part", "end_date", "term" ],
    # }

    # ### Build chain to structure raw text from trane pdf
    # llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
    # chain = create_extraction_chain(schema, llm)
    # messages = [{"role": "user", "content": output}]
    # trane_warranty = chain.run(messages)

    # Pydantic data class

    class Properties(BaseModel):
      model_number: str
      serial_number: str
      part: str
      end_date: str
      term: str

    # Build chain to structure raw text from trane pdf
    llm = AzureChatOpenAI(deployment_name="gpt35turbo",
                          model_name="gpt-35-turbo", temperature=0)
    chain = create_extraction_chain_pydantic(
        pydantic_schema=Properties, llm=llm)
    trane_warranty = chain.run(output)
    # print(lennox_warranty)

    trane_warranty = json.dumps(
        [warranty.__dict__ for warranty in trane_warranty])
    # lennox_warranty = json.dumps(lennox_warranty.__dict__)
    # print(lennox_warranty)

    trane_warranty = json.loads(trane_warranty)
    # print(lennox_warranty)

    print(trane_warranty)
    if trane_warranty:
      warranty_object = {}
      warranty_object["is_registered"] = True
      warranty_object["shipped_date"] = None
      warranty_object["install_date"] = None
      warranty_object["register_date"] = None
      warranty_object["manufacture_date"] = None
      warranty_object["model_number"] = None
      warranty_object["shipped_date"] = None
      warranty_object["last_name_match"] = False
      warranty_object["certificate"] = None
      # print(html)
      if "Congratulations, your Limited Warranty registration was successfully submitted" in str(html):
        warranty_object["last_name_match"] = True
      print(trane_warranty)
      warranties = [
          obj for obj in trane_warranty if obj['serial_number'] == serial_number]
      for warranty in warranties:
        # 06/22/2014
        end_date = warranty["end_date"]
        end_date = time.mktime(datetime.strptime(
            end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)

        term = warranty["term"]
        years = re.search(r"\d+", term).group()
        # print(int(years))
        years = int(years)
        # print(int(end_date))
        start_date = (datetime.fromtimestamp(end_date) -
                      relativedelta(years=years)).strftime("%m/%d/%Y")
        # 2021-04-01T00:00:00
        start_date = time.mktime(datetime.strptime(
            start_date, "%m/%d/%Y").timetuple())
        warranty["start_date"] = int(start_date)
        warranty_object["install_date"] = int(start_date)
        warranty_object["register_date"] = int(start_date)
        warranty_object["model_number"] = warranty["model_number"]
        warranty["name"] = warranty["part"].title()

        del warranty["part"]
        del warranty["term"]
        del warranty["model_number"]
        del warranty["serial_number"]
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
