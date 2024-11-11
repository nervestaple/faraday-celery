import time
import base64
import img2pdf
import io
import json
import os
import pdfplumber
import re
import redis
import requests
import boto3

from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as dateparse
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.callbacks import get_openai_callback
from langchain.chains import create_extraction_chain
from langchain.chains import create_extraction_chain_pydantic
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_loaders import OnlinePDFLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.utilities import SerpAPIWrapper
from PIL import Image
from pydantic import BaseModel
from serpapi.google_search import GoogleSearch
from tempfile import NamedTemporaryFile
from time import sleep
from typing import Sequence
from urllib.parse import urlparse
from utils import search_and_parse_pdfs
from uuid_extensions import uuid7str
from botocore.exceptions import NoCredentialsError

from celery_app import celery_app

load_dotenv()

# for future ref: check bradford white reg: https://warrantycenter.bradfordwhite.com/warranty/registrations-warranty/SC41081284


@celery_app.task
def get_bradford_white_warranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  def get_warranty_object(page):
    page.goto('https://warrantycenter.bradfordwhite.com/')
    page.locator("#check_serial_number").click()
    page.locator("#check_serial_number").fill(serial_number)
    page.locator("#check_btn").click()
    page.locator('.warranty-body').click()
    cells = page.locator('.warranty-body').locator('tr td:nth-child(3)').all()
    cell_data = [cell.text_content().strip() for cell in cells]
    if len(cell_data) < 8:
      return None

    serial, model, heater_type, mfg_date_str, original_mfg_date_str, warranty_length, warranty_expire_date_str, registration_status = cell_data

    mfg_date = dateparse(mfg_date_str)
    warranty_expire_date = dateparse(warranty_expire_date_str.replace('*', ''))
    install_date = (warranty_expire_date - relativedelta(years=6)).timestamp()

    return {
      "certificate": None,
      "install_date": install_date,
      "is_registered": registration_status != 'Not Registered',
      "last_name_match": False,
      "manufacture_date": mfg_date.timestamp(),
      "model_number": model,
      "register_date": None,
      "shipped_date": None,
      "warranties": [
          {
              "end_date": warranty_expire_date.timestamp(),
              "name": "Glass Lined Tank and Parts",
              "start_date": install_date
          }
      ]
    }

  warranty_object = scrape(get_warranty_object)

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": None}

  print({
      "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": None})
  if equipment_scan_id and equipment_scan_id is not (None):
    r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                      "warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": None}, timeout=30)
    print(r)

  if equipment_id and equipment_id is not (None):
    r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={
                      "warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": None}, timeout=30)
    print(r)


def scrape(scraper):
  from playwright.sync_api import sync_playwright

  with sync_playwright() as playwright:
    is_dev = os.getenv('ENVIRONMENT') == 'development'
    browser = playwright.chromium.launch(
      headless=(not is_dev), slow_mo=50 if is_dev else 0)
    context = browser.new_context()
    page = context.new_page()
    return scraper(page)
