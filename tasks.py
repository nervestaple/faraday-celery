from time import sleep
import os
import requests
import dotenv
from langchain.utilities import SerpAPIWrapper
from langchain.prompts import PromptTemplate
from langchain.agents import Tool
from langchain.chains import create_extraction_chain
import dotenv
from serpapi import GoogleSearch
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
import signal
from contextlib import contextmanager
from langchain.document_loaders import OnlinePDFLoader
from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils import search_and_parse_pdfs
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
from langchain.callbacks import get_openai_callback
import pdfplumber
from datetime import datetime
from tempfile import NamedTemporaryFile
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta
import json
import base64
from langchain.chains import create_extraction_chain_pydantic
from PIL import Image
import img2pdf
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from typing import Sequence
from celery import Celery
from celery.utils.log import get_task_logger

app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
logger = get_task_logger(__name__)

#from PIL import Image


class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


# try:
#     with time_limit(10):
#         long_function_call()
# except TimeoutException as e:
#     print("Timed out!")



@app.task
def identify_new_model(model_number, supporting_data):

  # url = "https://www.gemaire.com/rheem-ra1648aj1na-classic-4-ton-16-seer-condenser-208-230-volt-1-phase-60-hz-ra1648aj1na"

  # #loader = PlaywrightURLLoader(urls=[url], remove_selectors=["header", "footer"])
  # #loader = AsyncChromiumLoader([url])
  # loader = AsyncHtmlLoader([url])
  # #loader = SeleniumURLLoader([url])

  # print("starting to load html")
  # html = loader.load()
  # print(html)
  # print("waiting...")
  # time.sleep(10)
  # print(html)
  # return html
  # print("waiting...")
  # time.sleep(5)
  
  # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
  # r = requests.get(url, headers=headers)
  # print(r)
  # print(r.headers.get('content-type'))
  # return r

  # potential_resources = []
  # #loader = PlaywrightURLLoader(urls=["https://www.supplyhouse.com/Bradford-White-RG240T6N-40-Gallon-40000-BTU-Defender-Safety-System-Atmospheric-Vent-Energy-Saver-Residential-Water-Heater-Nat-Gas"])
  # #loader = AsyncChromiumLoader(["https://www.supplyhouse.com/Bradford-White-RG240T6N-40-Gallon-40000-BTU-Defender-Safety-System-Atmospheric-Vent-Energy-Saver-Residential-Water-Heater-Nat-Gas"])
  # loader = AsyncHtmlLoader([url])
      
  # print("starting to load html")
  # hostname = urlparse(url).hostname
  # html = loader.load()
  # print("waiting...")
  # time.sleep(10)
  # ### extract pdfs
  # scrape_html = html
  # #print(f"here is the html: {scrape_html}")
  # print(f"checking to see if list")
  # if isinstance(scrape_html, list):
  #   print(f"is list")
  #   scrape_html = next(iter(scrape_html))
  # if scrape_html:
  #   print(f"getting page content to scrape")
  #   scrape_html = scrape_html.page_content
  #   sopa = BeautifulSoup(scrape_html, "html.parser")
  #   #print(f"all links: {sopa.find_all('a')}")
  #   for link in sopa.find_all('a'):
  #     current_link = link.get('href')
  #     current_text = link.text
  #     if current_link:
  #       print(f"current link: {current_link}")
  #       if current_link.endswith('pdf') or "pdf" in current_text:
  #         if not(urlparse(current_link).hostname):
  #           potential_resources.append("https://" + hostname + current_link)
  #         else:
  #           potential_resources.append(current_link)
  # print(potential_resources)
  # return potential_resources

  with get_openai_callback() as cb:

    
    dotenv.load_dotenv()

    ### Create return variables for resource urls and related model numbers
    potential_resources = []
    resource_urls = []
    related_models = []
    bad_urls = []

    #model_number = "22V50F1"
    print(f"*** Starting new model search: {model_number}")

    ### Setup SerpAPI Tool
    params = {
        "gl": "us",
        "hl": "en",
    }
    search = SerpAPIWrapper(params=params)

    def serp_api_search(query):
      params = {
          "q": f"{query} -site:amazon.com -site:manualzz.com -site:yumpu.com -site:scribd.com -site:manualslib.com -site:goodmanparts.net -site:ebay.com -site:pinterest.com -site:manua.ls -site:usermanuals.au -site:manualsfile.com -site:manualowl.com -site:usedacdepot.com",
          "hl": "en",
          "gl": "us",
          "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
      }
      try:
        search_results = GoogleSearch(params)
        search_results = search_results.get_dict()
        if not(search_results.get("error")):
          if search_results.get('organic_results'):
            search_results = search_results['organic_results']
          else:
            raise Exception
        else:
          raise Exception
        return search_results[0:7]
      except Exception as e:
        print(f"Error: {e}")
        return None
        

      # try:
      #   search_results = search.run(query)
      # except Exception as e:
      #   print(f"Error: {e}")
      # else:
      #   return search_results
      # try:
      #   search_results = search.run(query)
      #   if not(search_results.get("error")):
      #     if search_results.get('organic_results'):
      #       search_results = search_results['organic_results']
      #     else:
      #       raise Exception
      #   else:
      #     raise Exception
      #   return search_results
      # except Exception as e:
      #   print(f"Error: {e}")

    search_tool = Tool.from_function(
      name="search tool",
      description="Useful for searching the internet to get answers",
      func=serp_api_search,
    )

    def check_valid_url(url):
      bad_url = 0
      headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
      print(f"checking to see if valid url: {url}")
      try:
        r = requests.get(url, timeout=30, headers=headers)
        print(r)
        if r.status_code == 200:
          print("good url")
          return r
        else:
          print("bad url")
      except Exception as e:
          print(f"Something went wrong {e}")
          bad_url += 1
          bad_urls.append(url)

    def parse_html(url):
      try:
        hostname = urlparse(url).hostname
        print(f"scraping url: {url}")
        print("starting to scrape")

        #loader = SeleniumURLLoader([url])
        #loader = PlaywrightURLLoader(urls=[url])
        loader = AsyncChromiumLoader([url])
        #loader = AsyncHtmlLoader([url])
      
        print("starting to load html")
        html = loader.load()
        print("waiting...")
        time.sleep(10)
        ### extract pdfs
        scrape_html = html
        #print(f"here is the html: {scrape_html}")
        print(f"checking to see if list")
        if isinstance(scrape_html, list):
          print(f"is list")
          scrape_html = next(iter(scrape_html))
        if scrape_html:
          print(f"getting page content to scrape")
          scrape_html = scrape_html.page_content
          sopa = BeautifulSoup(scrape_html, "html.parser")
          #print(f"all links: {sopa.find_all('a')}")
          counter = 0
          for link in sopa.find_all('a'):
            current_link = link.get('href')
            current_text = link.text
            if current_link:
              #print(f"current link: {current_link}")
              if current_link.endswith('pdf') or "pdf" in current_text:
                if not(urlparse(current_link).hostname):
                  potential_resources.append("https://" + hostname + current_link)
                  counter += 1
                else:
                  potential_resources.append(current_link)
                  counter += 1
            if counter >= 7:
              break
                
        #print(potential_resources)

        bs_transformer = BeautifulSoupTransformer()
        print("starting to parse html elements")
        docs_transformed = bs_transformer.transform_documents(html,tags_to_extract=["span", "p", "ul", "li", "h1", "h2", "h3", "h4", "dl", "dt", "tr"])
        # Grab the first 1000 tokens of the site
        #print(f"here are the docs: {docs_transformed}")
      
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=3500, 
                                                                        chunk_overlap=100)
        print("starting to split documents")
        #print(f"here is the docs: {docs_transformed}")
        splits = splitter.split_documents(docs_transformed)
        print("done splitting")
        #print(f"here are the splits: {splits}")
        if isinstance(splits, list):
          splits = next(iter(splits))
        if splits:
          text = splits.page_content
        else:
          text = ''
        print(f"here is the text: {text}")
        return text
        # if isinstance(splits, list):
        #   text = next(iter(splits))
        #   text = text.page_content
      except Exception as e:
        print(f"Error: {e}")
        bad_urls.append(url)
    
    def parse_pdf(url):
      bad_pdf = 0
      pdf_pages = []
      try:
          print("loading pdf")
          pdf_loader = PyPDFLoader(url)
          print("load and split")
          pdf_pages = pdf_loader.load_and_split()
          if len(pdf_pages) < 1:
            raise Exception("PDF was 0 pages")
      except Exception as e:
        print(f"something bad happended: {e}")
        try:
          print("trying a different loader")
          loader = OnlinePDFLoader(url)
          pdf_pages = loader.load()
          if len(pdf_pages) < 1:
            raise Exception("PDF was 0 pages")
        except Exception as e:
          print(f"something bad happended: {e}")
          bad_pdf += 1
          bad_urls.append(url)
          #continue  

      print(f"length of pdf is {len(pdf_pages)} pages")


      if len(pdf_pages) >= 1:
        potential_resources.append(url)
        ### Get full pdf in text
        text=''
        for page in pdf_pages:
            text += page.page_content
        
        print("starting split")

        ### Split text to limit tokens passed to LLM
        text_splitter = CharacterTextSplitter(
            separator = "\n",
            chunk_size = 3500,
            chunk_overlap  = 200,
            length_function = len,
        )
        texts = text_splitter.split_text(text)

        if isinstance(texts, list):
          texts = next(iter(texts))
        return texts
      
      else:
        bad_pdf += 1
        bad_urls.append(url)

       
      

    def parse_url(url):
      r = check_valid_url(url)
      if r:
        if r.headers.get('content-type') == 'application/pdf':
          print("this url is a pdf")
          text = parse_pdf(url)
          return text
        else:
          print("this url is not a pdf")
          text = parse_html(url)
          return text

    # Get equipment types from database
    equipment_types = []
    r = requests.get('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/equipmentiq_types', timeout=30).json()
    for type in r:
      equipment_types.append(type["name"])
    


    # Get equipment manufacturers from database
    equipment_manufacturers = []
    r = requests.get('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/equipmentiq_manufacturers', timeout=30).json()
    for manufacturer in r:
      equipment_manufacturers.append(manufacturer["name"])

    #print(equipment_manufacturers)

    # base_equipment_info_search_prompt = PromptTemplate(
    #     input_variables=["model_number", "supporting_data"],
    #     template='''Using the model number, supporting data listed below determine each of the items in "Information to provide". Provide only the information below in bulletpoint format and nothing else. If you can't determine one of the fields below return "null" for each except for model number. Use

    #     Information to provide:
    #     - model number (return the model number given below. If model number returns no information during search. Try replacing any 1 with I and replacing any I with 1, and replacing any 0 with O and replacing any O with 0)
    #     - manufacturer (Determine the manufacturer using the manufacturer options below, if the manufacturer isnt in the list below return null)
    #     - name (this could be a series name. If you can't find one, just return the model number)
    #     - equipment type (Determine the equipment type using only the "Equipment types options" list below. If you can't match the equipment type to one of the "Equipment types options" list below then return null.)

    #     Equipment type options:
    #     - air conditioner (display "air conditioner for "condenser" "condensing unit", or "condenser unit")
    #     - package unit
    #     - heat pump
    #     - water heater
    #     - humidifer
    #     - furnace (return "furnace" for "gas furnace")
    #     - boiler (return "boiler" for "condensing boiler", "gas boiler", or "propane boiler")
    #     - air filter
    #     - thermostat (return "thermostat" for "controls" or "sensors")
    #     - exhaust fan
    #     - air handler
    #     - evaporator coil
    #     - UV air cleaner
    #     - electronic air cleaner
    #     - heat strip (return "heat strip" for "heat kit", "electric heat", or "eletric heat element")
    #     - indoor coil
    #     - compressor


    #     Manufacturer options:
    #     - Trane
    #     - Lennox
    #     - Carrier
    #     - Rheem
    #     - Ruud
    #     - Daikin
    #     - Goodman
    #     - International Comfort Products (ICP)
    #     - York
    #     - A.O. Smith (or AO Smith)
    #     - Bryant
    #     - Amana
    #     - Nordyne
    #     - Copeland
    #     - AprilAire


    #     model number: {model_number}
    #     supporting data: {supporting_data}

    #     Reminder: Once you've determined the final answer, stop executing and provide only the bulletpoint list. Do not proceed with any other actions.

    #     Here are some examples of final answers. These are only examples. Don't use them as part of the question:
    #     - model number: GSX140371KD
    #     - manufacturer: Goodman
    #     - name: GSX140371KD
    #     - equipment type: air conditioner

    #     - model number: RA1648AJINA
    #     - manufacturer: Rheem
    #     - name: RA1648AJINA
    #     - equipment type: air conditioner

    #     - model number: RL751 (REU-VC2528FFUD-US (A))
    #     - manufacturer: Rinnai
    #     - name: RL75iN RL Model Series
    #     - equipment type: water heater

    #     - model number: TUH1B080A9421AA
    #     - manufacturer: Trane
    #     - name: XR95
    #     - equipment type: furnace

    #     - model number: 1234566
    #     - manufacturer: null
    #     - name: null
    #     - equipment type: null
    #     - sources: null
    #     '''
    # )

    search_results = serp_api_search(model_number)
    urls = []
    if search_results:
      for search_result in search_results:
        urls.append({"url": search_result["link"]})
    else:
      search_results = serp_api_search(f"{model_number} {supporting_data}")
      if search_results:
        for search_result in search_results:
          urls.append({"url": search_result["link"]})
      else:
        urls = None
        
    print(urls)
    
    # base_equipment_info_search_prompt = PromptTemplate(
    #     input_variables=["model_number", "supporting_data"],
    #     template='''Use the search tool return a list of only urls related to the model number and supporting data ordered by the likeliness that the url contains relevant information like manufacturer, model, and type of equipment for the model number and supporting data provided below.
        
    #     First search using just the model number provided. If you can't find any urls using just the model number trying searching using the model number and supporting data provided below with the search tool. If you still can't find any urls after searching with both the model nummber and supporting data stop the search and return "null":

    #     model number: {model_number}
    #     supporting data: {supporting_data}

    #     Reminder: Once you've determined the final answer, stop executing and provide only the list of urls. Do not proceed with any other actions. If you the search tool doesn't return any results, return "null" and nothing else.
    #     '''
    # )


    # ### Create agent for internet search task
    # llm = AzureChatOpenAI(deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
    # tools = [search_tool]
    # agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True, max_execution_time=120)
    # prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data)
    # messages = [{"role": "user", "content": prompt}]
    # # print(messages)

    # ### Get output from internet search task
    # print("** begin run")
    # try:
    #   model_object = {'model_number': model_number}
    #   output = agent.run(messages)
    # except Exception as e:
    #   print(f"something went wrong: {e}")
    #   output = None
    # else:
    #   print("** begin output")
    #   print(output)
    #   print("** end output")
    #   #return output

    # if output and output != "null":
      
    #   schema = {
    #     "properties": {
    #         "url": {"type": "string"},
    #     },
    #     "required": ["url"],
    #   }

    #   llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
    #   chain = create_extraction_chain(schema, llm)
    #   messages = [{"role": "user", "content": output}]
    #   urls = chain.run(messages)
    #   print(urls)

    base_equipment_info_search_prompt = PromptTemplate (
      input_variables=["model_number", "supporting_data", "text", "equipment_types", "equipment_manufacturers"],
      template='''Using the model number and supporting data search through the text provided below determine each of the items in "Information to provide". Provide only the information below in bulletpoint format and nothing else. If you can't determine one of the fields below return "null" for each except for model number.

      Information to provide:
      - model number (return the model number given below. If model number returns no information during search. Try replacing any 1 with I and replacing any I with 1, and replacing any 0 with O and replacing any O with 0)
      - manufacturer (Determine the manufacturer using the manufacturer options list below and return the corresponding id number. Ff the manufacturer isnt in the list below return null)
      - name (this could be a series name. If you can't find one, just return the model number)
      - equipment type (Determine the equipment type from the "Equipment types options" list below and return the corresponding id number. If you can't match the equipment type to one of the "Equipment types options" list below then return null.)

      Equipment type options:
      {equipment_types}


      Manufacturer options:
      {equipment_manufacturers}


      model number: {model_number}
      supporting data: {supporting_data}
      text: {text}

      Reminder: Once you've determined the final answer, stop executing and provide only the bulletpoint list. Do not proceed with any other actions.

      Here are some examples of final answers. These are only examples. Don't use them as part of the question:
      - model number: GSX140371KD
      - manufacturer: Goodman
      - name: GSX140371KD
      - equipment type: Air Conditioner

      - model number: RA1648AJINA
      - manufacturer: Rheem
      - name: RA1648AJINA
      - equipment type: Air Conditioner

      - model number: RL75i (REU-VC2528FFUD-US (A)
      - manufacturer: Rinnai
      - name: RL75iN RL Model Series
      - equipment type: Water Heater

      - model number: TUH1B080A9421AA
      - manufacturer: Trane
      - name: XR95
      - equipment type: Furnace

      - model number: LRP16GX48-108VP-3A
      - manufacturer: Lennox
      - name: LRP
      - equipment type: Package Unit

      - model number: 1234566
      - manufacturer: null
      - name: null
      - equipment type: null
      '''
    )

    texts = ""

    counter = 0
    for url in urls:
      valid_url = check_valid_url(url["url"])
      if valid_url:
        print(f"parsing url: {url}")
        text = parse_url(url["url"])
        if text:
          counter += 1
          texts += text
      if counter == 3:
        break
      #url = "https://www.ferguson.com/product/american-standard-hvac-4wcc3-series-5-ton-13-seer-convertible-r-410a-packaged-heat-pump-a4wcc3060a1000a/2757673.html"
      #url = "https://python.langchain.com/docs/use_cases/web_scraping"
      #text = parse_url(url)
      
    print(f"here is the text: {texts}")
    ### Create agent for internet web search
    llm = AzureChatOpenAI(deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
    #prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
    chain = LLMChain(llm=llm, prompt=base_equipment_info_search_prompt)
    output = chain.run({
          'model_number': model_number,
          'supporting_data': supporting_data,
          'text': texts,
          'equipment_types': equipment_types,
          'equipment_manufacturers': equipment_manufacturers
          })
    print(output)
    
    schema = {
        "properties": {
            "model_number": {"type": "string"},
            "manufacturer": {"type": "string"},
            "equipment_type": {"type": "string"},
            "name": {"type": "string"},
        },
        "required": ["model_number", "manufacturer", "equipment_type"],
    }

    ### Build chain to structure raw text from internet search
    llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
    chain = create_extraction_chain(schema, llm)
    messages = [{"role": "user", "content": output}]
    model_object = chain.run(messages)
    print(model_object)
    if isinstance(model_object, list):
      model_object = next(iter(model_object))
    
    ### IF AC
    
    if model_object.get("equipment_type") == "1" or model_object.get("equipment_type") == "13" or model_object.get("equipment_type") == "14" or model_object.get("equipment_type") == "16" or model_object.get("equipment_type") == "17" or model_object.get("equipment_type") == "18" or model_object.get("equipment_type") == "22" or model_object.get("equipment_type") == "38" or model_object.get("equipment_type") == "39":
      ac_search_prompt = PromptTemplate(
        input_variables=["model_number", "equipment_type", "manufacturer", "text"],
        template='''Using the manufacturer, model number, and equipment type search through the text provided below to determine each of the items in "Information to provide." Provide only the information below in bulletpoint format and nothing else. If you can't determine one of the fields below return "null" for each.

        Information to provide:
        - btus (also known as british thermal units or btuh or Nominal Capacity in 000s of BTUs. It may be listed in the following formats: 36, 36,000, 36K, 36000. btus can also be found by decoding the model number or converting the tonnage.)
        - tonnage (tonnage also known as tons can be found by decoding the model number or converting btus to tons)
        - SEER (example: 21)
        - EER (example: 14)
        - refrigerant (examples: R-410A, R-22)
        - voltage (also known as volts. examples: 208/230V-1ph-60hz, 115V-1ph-60hz, 120V-1ph-60hz, 200/230V-1ph-60hz)
        - type (Only provide the type from the list of "Air Conditioner type options" below. If you can't match the equipment type to one of the "Air Conditioner type options" below then return null.)
        - heat pump (set to true if model number is a heat pump. otherwise, set to false)
        - component (Only provide the component from the list of "Air conditioner component options" below. If you can't match the component to one of the "Air conditioner component options" below then return null.)
        - application (Only provide the application from the list of "Air conditioner application options" below. If you can't match the application to one of the "Air conditioner application options" below then return null.)
        If you can't determine one of the fields above return null.

        Air conditioner type options:
        - split system
        - ductless / mini split (also referred to as "multi-split")
        - package unit
        - evaporative cooler

        Air conditioner component options:
        - condenser
        - air handler
        - indoor unit (also known as "wall mounted unit" or "casette")
        - evaporator coil
        - compressor

        Air conditioner application options:
        - residential
        - commercial

        model number: {model_number}
        equipment_type: {equipment_type}
        manufacturer: {manufacturer}
        text: {text}

        Here are some examples of final answers. These are only examples. Don't use them as part of the question:
        - btus: 18000
        - tonnage: 1.5
        - seer: 14
        - eer: null
        - refrigerant: R-410A
        - voltage: 208/230V-1ph-60hz
        - type: split system
        - component: condenser
        - application: residential
        - heat pump: true

        
        - btus: 46000
        - tonnage: 4
        - seer: 16
        - eer: 12.5
        - refrigerant: R-410A
        - voltage: 208/230V-1ph-60hz
        - type: split system
        - component: condenser
        - application: residential
        - heat pump: true

        
        - btus: 40500
        - tonnage: 3.5
        - seer: 13
        - eer: null
        - refrigerant: R-410A
        - voltage: 208/230V-1ph-60hz
        - type: package unit
        - component: null
        - application: commercial
        - heat pump: false


        - btus: 40500
        - tonnage: 3.5
        - seer: null
        - eer: null
        - refrigerant: null
        - voltage: null
        - type: null
        - component: null
        - application: null
        - heat pump: false
        '''
      )

      print("starting AC data search")
      print(f"here is the text to seach through: {texts}")

      ### Create agent for internet web search
      llm = AzureChatOpenAI(deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
      #prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
      chain = LLMChain(llm=llm, prompt=ac_search_prompt)
      output = chain.run({
            'model_number': model_object.get("model_number"),
            'manufacturer': model_object.get("manufacturer"),
            'equipment_type': model_object.get("equipment_type"),
            'text': texts
            })
      
      
      ### Set schema to structure internet search data in JSON
      schema = {
        "properties": {
          "air_conditioning_btus": {"type": "integer"},
          "air_conditioning_tonnage": {"type": "integer"},
          "air_conditioning_seer": {"type": "string"},
          "air_conditioning_eer": {"type": "string"},
          "air_conditioning_refrigerant": {"type": "string"},
          "air_conditioning_voltage": {"type": "string"},
          "air_conditioning_type": {"type": "string"},
          "air_conditioning_component": {"type": "string"},
          "air_conditioning_application": {"type": "string"},
          "air_conditioning_heat_pump": {"type": "boolean"},
        },
        "required": ["air_conditioning_btus", "air_conditioning_tonnage", "air_conditioning_heat_pump", "air_conditioning_type"],
      }
      
      ### Build chain to structure raw text from internet search
      llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = create_extraction_chain(schema, llm)
      messages = [{"role": "user", "content": output}]
      ac_object = chain.run(messages)
      
      ### Get first object returned by extraction chain
      if isinstance(ac_object, list):
        ac_object = next(iter(ac_object))
      print(ac_object)
      model_object.update(ac_object)
      print(f'''*** Here is structured data for AC: {model_number}:
        {model_object}
        ''')
  
    ### IF WH

    elif model_object.get("equipment_type") == "3":
      
      print("water heater")
      wh_search_prompt = PromptTemplate(
          input_variables=["model_number", "equipment_type", "manufacturer", "text"],
          template='''Using the manufacturer, model number, equipment type, and text listed below determine each of the items in "Information to provide." Provide only the information below in bulletpoint format and nothing else. If you can't determine one of the fields below return "null" for each.

          Information to provide:
          - type (Only provide the type from the list of "Water heater type options" below. If you can't match the type to one of the "Water heater type options" below then return null)
          - btus (also known as british thermal units or btuh, may be listed in the following formats: 75,000, 75K, 75000)
          - gallons (also know as Rated Nominal Volume (Gallons))
          - fuel (Only provide the type from the list of "Water heater fuel options" below. If you can't match the fuel to one of the "Water heater fuel options" below then return null)
          If you can't determine one of the fields above return null

          Water heater type options:
          - tankless
          - standard

          Water heater fuel options:
          - natural gas
          - liquid propane
          - electric

          model number: {model_number}
          equipment_type: {equipment_type}
          manufacturer: {manufacturer}
          text: {text}
          '''
        )
      ### Create agent for internet search task
      llm = AzureChatOpenAI(deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
      #prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
      chain = LLMChain(llm=llm, prompt=wh_search_prompt)
      output = chain.run({
            'model_number': model_object.get("model_number"),
            'manufacturer': model_object.get("manufacturer"),
            'equipment_type': model_object.get("equipment_type"),
            'text': texts
            })
      
      #return output

        
      ### Set schema to structure internet search data in JSON
      schema = {
        "properties": {
          "water_heater_btus": {"type": "integer"},
          "water_heater_gallons": {"type": "string"},
          "water_heater_type": {"type": "string"},
          "water_heater_fuel": {"type": "string"},
        }
      }
        
      ### Build chain to structure raw text from internet search
      llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = create_extraction_chain(schema, llm)
      messages = [{"role": "user", "content": output}]
      wh_object = chain.run(messages)
      #print(wh_object)
      
      ### Get first object returned by extraction chain
      if isinstance(wh_object, list):
        wh_object = next(iter(wh_object))
      #print(wh_object)
      model_object.update(wh_object)
      print(f'''*** Here is structured data for WH: {model_number}:
          {model_object}
          ''')
      
      ### IF Furnace

    elif model_object.get("equipment_type") == "2":
      print("furnace")
      fur_search_prompt = PromptTemplate(
          input_variables=["model_number", "equipment_type", "manufacturer", "text"],
          template='''Using the manufacturer, model number, equipment type, and text listed below determine each of the items in "Information to provide." Provide only the information below in bulletpoint format and nothing else. If you can't determine one of the fields below return "null" for each.

          Information to provide:
          - btus (also known as british thermal units or btuh, may be listed in the following formats: 75,000, 100K, 80000 or heating capacity)
          - AFUE (also known as Annual Fuel Utilization Efficiency, examples: 80%, 95%)
          - voltage (examples: 208/230V-1ph-60hz, 115V-1ph-60hz, 120V-1ph-60hz, 200/230V-1ph-60hz, 200/230V-3ph-60hz, 460V-3ph-60hz)
          - fuel (Only provide the type from the list of "Furnace fuel options" below. If you can't match the fuel to one of the "Furnace fuel options" below then return null)
          

          Furnace fuel options:
          - natural gas
          - liquid propane

          model number: {model_number}
          equipment_type: {equipment_type}
          manufacturer: {manufacturer}
          text: {text}
          '''
        )
      
      ### Create agent for internet search task
      llm = AzureChatOpenAI(deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
      #prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
      chain = LLMChain(llm=llm, prompt=fur_search_prompt)
      output = chain.run({
            'model_number': model_object.get("model_number"),
            'manufacturer': model_object.get("manufacturer"),
            'equipment_type': model_object.get("equipment_type"),
            'text': texts
            })
      
      # ### Get output from internet search task
      # print("** begin run")
      # fur_attempts = 0
      # try:
      #   output = agent.run(messages)
      # except Exception as e:
      #   print(f"something went wrong: {e}")
      # else:
      #   print("** begin output")
      #   print(output)
      #   print("** end output")
        
        ### Set schema to structure internet search data in JSON
      schema = {
        "properties": {
          "furnace_btus": {"type": "integer"},
          "furnace_tonnage": {"type": "string"},
          "furnace_afue": {"type": "integer"},
          "furnace_voltage": {"type": "string"},
          "furnace_fuel": {"type": "string"},
        }
      }
      
      ### Build chain to structure raw text from internet search
      llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = create_extraction_chain(schema, llm)
      messages = [{"role": "user", "content": output}]
      fur_object = chain.run(messages)
      #print(fur_object)
      
      ### Get first object returned by extraction chain
      if isinstance(fur_object, list):
        fur_object = next(iter(fur_object))
      #print(wh_object)
      model_object.update(fur_object)
      print(f'''*** Here is structured data for FUR: {model_number}:
          {model_object}
          ''')


    ### END Internet Search Process

    ### START PDF Search process

    ### Only run if model has been marked as verified
    if not(model_object.get("model_number") == None) and not(model_object.get("manufacturer") == None) and not(model_object.get("equipment_type") == None):
        #print(model_object)
        
        ### Setup SERP API Tool for product data pdf search
        params = {
          "q": f"{model_number} product data pdf",
          "hl": "en",
          "gl": "us",
          "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
        }
        pdf_search = GoogleSearch(params)

        ### Run pdf search
        results = pdf_search.get_dict()
        #print(results['organic_results'])

        #print(results)

        if not(results.get("error")):
          if results.get('organic_results'):
            results = results['organic_results']

          print("start pdfs")
          print(f"potential resources: {potential_resources}")
          search_results = search_and_parse_pdfs(results, model_number, resource_urls, related_models, potential_resources, bad_urls)
          print("done")
        else:
          print("no search results")

        
        if not(any(url['type'] == "Installation Manual" for url in resource_urls)):
            params = {
              "q": f"{model_number} install manual pdf",
              "hl": "en",
              "gl": "us",
              "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
            }
            pdf_search = GoogleSearch(params)

            ### Run pdf search
            results = pdf_search.get_dict()
            #print(results['organic_results'])


            if not(results.get("error")):
              if results.get('organic_results'):
                results = results['organic_results']
            
              print("start install manual pdfs")
              print(f"bad urls: {bad_urls}")
              search_results = search_and_parse_pdfs(results, model_number, resource_urls, related_models, [], bad_urls)
              print("done")
            else:
              print("no search results")

        if not(any(url['type'] == "Owners Manual" for url in resource_urls)):
            params = {
              "q": f"{model_number} owners manual pdf",
              "hl": "en",
              "gl": "us",
              "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
            }
            pdf_search = GoogleSearch(params)

            ### Run pdf search
            results = pdf_search.get_dict()
            #print(results['organic_results'])

            if not(results.get("error")):
              if results.get('organic_results'):
                results = results['organic_results']
            
              print("start owners manual pdfs")
              search_results = search_and_parse_pdfs(results, model_number, resource_urls, related_models, [], bad_urls)
              print("done last")
            else:
              print("no search results")

        ### remove duplicate resources
        if resource_urls:
          unique_resources = [resource_urls[0]]
          for resource in resource_urls:
              if resource not in unique_resources:
                  unique_resources.append(resource)

          resource_urls = unique_resources


        ### remove duplicate related_models
        if related_models:
          unique_related_models = [related_models[0]]
          for model in related_models:
              if model not in unique_related_models:
                  unique_related_models.append(model.strip())

          related_models = unique_related_models

        ### set pdf manual variables
        product_data = next((url for url in resource_urls if url['type'] == "Product Data"), None)
        if product_data is not(None):
          model_object["product_data"] = product_data["url"]

        iom = next((url for url in resource_urls if url['type'] == "Installation Manual"), None)
        if iom is not(None):
          model_object["iom"] = iom["url"]

        owners_manual = next((url for url in resource_urls if url['type'] == "Owners Manual"), None)
        if owners_manual is not(None):
          model_object["owners_manual"] = owners_manual["url"]

        service_manual = next((url for url in resource_urls if url['type'] == "Service Manual"), None)
        if service_manual is not(None):
          model_object["service_manual"] = service_manual["url"]

        wiring_diagram = next((url for url in resource_urls if url['type'] == "Wiring Diagram"), None)
        if wiring_diagram is not(None):
          model_object["wiring_diagram"] = wiring_diagram["url"]

        specs = next((url for url in resource_urls if url['type'] == "Equipment Specs"), None)
        if specs is not(None):
          model_object["specs"] = specs["url"]


        model_object["resources"] = resource_urls
        model_object["related_models"] = related_models
        
        print(model_object)
    
      
    else:
        print("error")

    model_object["openai_data"] = {"total_tokens": cb.total_tokens, "prompt_tokens": cb.prompt_tokens, "completion_tokens": cb.completion_tokens, "total_cost": cb.total_cost}
    r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/equipmentiq_upload_new_model', json={"model_object": model_object}, timeout=30)
    print(f"Status Code: {r.status_code}, Response: {r.json()}, Model: {model_object}")
    print(f"Model: {model_object}")
    print(f"Total Tokens: {cb.total_tokens}")
    print(f"Prompt Tokens: {cb.prompt_tokens}")
    print(f"Completion Tokens: {cb.completion_tokens}")
    print(f"Total Cost (USD): ${cb.total_cost}")
    return model_object

## GET CARRIER WARRANTY
@app.task
def getCarrierWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  
  print(f"### Starting Carrier Warranty Lookup: {serial_number}")

  from playwright.sync_api import Playwright, sync_playwright, expect


  def run(playwright: Playwright) -> None:
      html = None
      pdf = None
      browser = playwright.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      page.goto(f"https://www.carrierenterprise.com/warranty/{serial_number}")
      try:
        #print(page.get_by_role("heading", name="Select Model"))
        page.get_by_role("heading", name="Select Model").click()
        #print(page.locator(".main-page-2b_").get_by_role("list").get_by_role("link").all())
        page.locator(".main-page-2b_").get_by_role("list").get_by_role("link").nth(0).click()

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
          page.query_selector(".wrapPanel-root-3px").screenshot(path=img_temp_file.name)
          image = Image.open(img_temp_file.name)
          pdf_bytes = img2pdf.convert(image.filename)
          pdf = open(pdf_temp_file.name, "wb")
          pdf.write(pdf_bytes)
          pdf.close()
          img_temp_file.flush()
          pdf_temp_file.flush()
        except Exception as e:
          print(f"something went wrong: {e}")

      except Exception as e:
        print(f"something went wrong: {e}")
      #print(html)
    

      # ---------------------
      context.close()
      browser.close()
      return {"html": html, "pdf": pdf_temp_file.file}

      


  html = None
  pdf = None
  with sync_playwright() as playwright:
      result = run(playwright)
      if result is not(None):
        html = result["html"]
        pdf = result["pdf"]


#   html = '''
# <div class="wrapContainer-root-XJZ"></div>
# <div class="wrapContainer-root-XJZ">
#   <div class="wrapPanel-root-3px ">
#     <div class="wrapLiner-root-1xh ">
#       <div class="pageTitle-root-17a ">
#         <div class="pageTitle-titleRow-1ur">
#           <div>
#             <h1 class="heading-h1-10V m-b-0">Warranty</h1>
#           </div>
#         </div>
#       </div>
#       <p class="lead-root-3bJ ">Check warranty status for Carrier, Bryant, and Payne equipment.</p>
#       <form>
#         <div class="field-root-2gS   "><label class="label-root-25h " for="serial_number">Serial Number<span
#               aria-label="Required" class="inputRequired-root-IpO">*</span></label>
#           <div class="field-inputWrap-Tdf"><span class="fieldIcons-root-30W null"
#               style="--iconsBefore: 0; --iconsAfter: 0;"><span class="fieldIcons-input-2tr"><input
#                   class="textInput-input-BvJ   textInput-input_height_base-3_z textInput-input_maxWidth_base-12k "
#                   id="serial_number" placeholder="Ex: 12345" type="text" name="serial_number"
#                   value="1715X37608"></span><span class="fieldIcons-before-DYA"></span><span
#                 class="fieldIcons-after-22G"></span></span>
#             <div class="inputHint-root-16I ">Only available for Carrier, Bryant, and Payne equipment.</div>
#           </div>
#         </div>
#         <div class="actionGroup-root_left-saM actionGroup-root-1p7 "><button
#             class=" button-root-16x button-root_size_base-Q7M  " type="submit">Check Warranty</button><a
#             class=" button-root-16x button-root_size_base-Q7M  button-root_secondary-2MQ"
#             href="/servicebench">ServiceBench®</a></div>
#       </form>
#       <h2 class="heading-h2-3Rs ">Serial Number: 1715X37608</h2>
#       <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ table-root_zebraDark--yC  ">
#         <tbody>
#           <tr>
#             <th>Name</th>
#             <td>CASED VERT N-ALUM</td>
#           </tr>
#           <tr>
#             <th>Model Number</th>
#             <td>
#               <div class="actionGroup-root_left-saM actionGroup-root-1p7 m-b-0"><span>CNPVP3617ALA</span><a
#                   class=" button-root-16x button-root_size_s-2cU  button-root_secondary-2MQ"
#                   href="/part-finder/CNPVP3617ALA">View Parts</a></div>
#             </td>
#           </tr>
#           <tr>
#             <th>Owner</th>
#             <td>Donte Whitner</td>
#           </tr>
#           <tr>
#             <th>Equipment Installation Address</th>
#             <td>473 Pierson Dr,Richmond Heights,OH44143,US</td>
#           </tr>
#           <tr>
#             <th>Date Installed</th>
#             <td class="text-nowrap">2015-05-07</td>
#           </tr>
#         </tbody>
#       </table>
#       <h2 class="heading-h2-3Rs ">Entitlement Overview</h2>
#       <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ table-root_zebraDark--yC  ">
#         <tbody>
#           <tr>
#             <th>Discrete Model Number</th>
#             <td>CNPVP3617ALAAAAA</td>
#           </tr>
#           <tr>
#             <th>Warranty Policy Code</th>
#             <td>CP115AL</td>
#           </tr>
#           <tr>
#             <th>Warranty Policy Description</th>
#             <td>FOR SPECIFIC COVERAGE ON NON-REGISTERED UNITS INSTALLED IN OWNER OCCUPIED, NON-OWNER OCCUPIED AND
#               COMMERCIAL APPLICATIONS, REFER TO WARRANTY CERTIFICATE</td>
#           </tr>
#           <tr>
#             <th>Standard Labor Warranty Expiration Date</th>
#             <td></td>
#           </tr>
#           <tr>
#             <th>Standard Part Warranty Expiration Date</th>
#             <td></td>
#           </tr>
#           <tr>
#             <th>UTC Property ID</th>
#             <td></td>
#           </tr>
#           <tr>
#             <th>Marked As</th>
#             <td></td>
#           </tr>
#           <tr>
#             <th>Shipped Date</th>
#             <td class="text-nowrap">2015-04-29</td>
#           </tr>
#           <tr>
#             <th>Replacement Of Model Number</th>
#             <td></td>
#           </tr>
#           <tr>
#             <th>Replacement Of Serial Number</th>
#             <td></td>
#           </tr>
#         </tbody>
#       </table>
#       <h2 class="heading-h2-3Rs ">Warranty Info (All)</h2>
#       <div class=" ">
#         <div>
#           <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ  table-root_zebraLight-11Q ">
#             <thead>
#               <tr>
#                 <th>Component Code</th>
#                 <th>Warranty Length</th>
#                 <th>Installed After</th>
#                 <th>Warranty Start</th>
#                 <th>Warranty Stop</th>
#                 <th>Application Type</th>
#                 <th>Brand</th>
#               </tr>
#             </thead>
#             <tbody>
#               <tr>
#                 <td>Enhanced Exchange Product Warranty</td>
#                 <td>10 years</td>
#                 <td class="text-nowrap">2009-02-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2025-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Exchange Product Warranty</td>
#                 <td>5 years</td>
#                 <td class="text-nowrap">2009-02-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2020-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Enhanced Parts Warranty</td>
#                 <td>10 years</td>
#                 <td class="text-nowrap">2009-02-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2025-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Standard Parts Warranty</td>
#                 <td>5 years</td>
#                 <td class="text-nowrap">2012-01-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2020-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Exchange Product Warranty</td>
#                 <td>5 years</td>
#                 <td class="text-nowrap">2012-01-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2020-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#             </tbody>
#           </table>
#         </div>
#       </div>
#       <h2 class="heading-h2-3Rs ">Warranty Info (Original)</h2>
#       <div class=" ">
#         <div>
#           <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ  table-root_zebraLight-11Q ">
#             <thead>
#               <tr>
#                 <th>Component Code</th>
#                 <th>Warranty Length</th>
#                 <th>Installed After</th>
#                 <th>Warranty Start</th>
#                 <th>Warranty Stop</th>
#                 <th>Application Type</th>
#                 <th>Brand</th>
#               </tr>
#             </thead>
#             <tbody>
#               <tr>
#                 <td>Enhanced Exchange Product Warranty</td>
#                 <td>10 years</td>
#                 <td class="text-nowrap">2009-02-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2025-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Exchange Product Warranty</td>
#                 <td>5 years</td>
#                 <td class="text-nowrap">2009-02-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2020-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Enhanced Parts Warranty</td>
#                 <td>10 years</td>
#                 <td class="text-nowrap">2009-02-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2025-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#             </tbody>
#           </table>
#         </div>
#       </div>
#       <h2 class="heading-h2-3Rs ">Warranty Info (Subsequent)</h2>
#       <div class=" ">
#         <div>
#           <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ  table-root_zebraLight-11Q ">
#             <thead>
#               <tr>
#                 <th>Component Code</th>
#                 <th>Warranty Length</th>
#                 <th>Installed After</th>
#                 <th>Warranty Start</th>
#                 <th>Warranty Stop</th>
#                 <th>Application Type</th>
#                 <th>Brand</th>
#               </tr>
#             </thead>
#             <tbody>
#               <tr>
#                 <td>Standard Parts Warranty</td>
#                 <td>5 years</td>
#                 <td class="text-nowrap">2012-01-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2020-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#               <tr>
#                 <td>Exchange Product Warranty</td>
#                 <td>5 years</td>
#                 <td class="text-nowrap">2012-01-01</td>
#                 <td class="text-nowrap">2015-05-07</td>
#                 <td class="text-nowrap">2020-05-07</td>
#                 <td>Owner Occupied Residential</td>
#                 <td>ALL</td>
#               </tr>
#             </tbody>
#           </table>
#         </div>
#       </div>
#     </div>
#   </div>
# </div>

#   '''

#   html = '''
# <main class="main-page-2b_">
#   <div class="wrapContainer-root-XJZ"></div>
#   <div class="wrapContainer-root-XJZ">
#     <div class="wrapPanel-root-3px ">
#       <div class="wrapLiner-root-1xh ">
#         <div class="pageTitle-root-17a ">
#           <div class="pageTitle-titleRow-1ur">
#             <div>
#               <h1 class="heading-h1-10V m-b-0">Warranty</h1>
#             </div>
#           </div>
#         </div>
#         <p class="lead-root-3bJ ">Check warranty status for Carrier, Bryant, and Payne equipment.</p>
#         <form>
#           <div class="field-root-2gS   "><label class="label-root-25h " for="serial_number">Serial Number<span
#                 aria-label="Required" class="inputRequired-root-IpO">*</span></label>
#             <div class="field-inputWrap-Tdf"><span class="fieldIcons-root-30W null"
#                 style="--iconsBefore: 0; --iconsAfter: 0;"><span class="fieldIcons-input-2tr"><input
#                     class="textInput-input-BvJ   textInput-input_height_base-3_z textInput-input_maxWidth_base-12k "
#                     id="serial_number" placeholder="Ex: 12345" type="text" name="serial_number"
#                     value="1715X3760"></span><span class="fieldIcons-before-DYA"></span><span
#                   class="fieldIcons-after-22G"></span></span>
#               <div class="inputHint-root-16I ">Only available for Carrier, Bryant, and Payne equipment.</div>
#             </div>
#           </div>
#           <div class="actionGroup-root_left-saM actionGroup-root-1p7 "><button
#               class=" button-root-16x button-root_size_base-Q7M  " type="submit">Check Warranty</button><a
#               class=" button-root-16x button-root_size_base-Q7M  button-root_secondary-2MQ"
#               href="/servicebench">ServiceBench®</a></div>
#         </form>
#         <p>Serial number not found.</p>
#       </div>
#     </div>
#   </div>
# </main>
# '''

  # html = '''
  # <main class="main-page-2b_">
  #   <div class="wrapContainer-root-XJZ"></div>
  #   <div class="wrapContainer-root-XJZ">
  #     <div class="wrapPanel-root-3px ">
  #       <div class="wrapLiner-root-1xh ">
  #         <div class="pageTitle-root-17a ">
  #           <div class="pageTitle-titleRow-1ur">
  #             <div>
  #               <h1 class="heading-h1-10V m-b-0">Warranty</h1>
  #             </div>
  #           </div>
  #         </div>
  #         <p class="lead-root-3bJ ">Check warranty status for Carrier, Bryant, and Payne equipment.</p>
  #         <form>
  #           <div class="field-root-2gS   "><label class="label-root-25h " for="serial_number">Serial Number<span
  #                 aria-label="Required" class="inputRequired-root-IpO">*</span></label>
  #             <div class="field-inputWrap-Tdf"><span class="fieldIcons-root-30W null"
  #                 style="--iconsBefore: 0; --iconsAfter: 0;"><span class="fieldIcons-input-2tr"><input
  #                     class="textInput-input-BvJ   textInput-input_height_base-3_z textInput-input_maxWidth_base-12k "
  #                     id="serial_number" placeholder="Ex: 12345" type="text" name="serial_number"
  #                     value="1314A86771"></span><span class="fieldIcons-before-DYA"></span><span
  #                   class="fieldIcons-after-22G"></span></span>
  #               <div class="inputHint-root-16I ">Only available for Carrier, Bryant, and Payne equipment.</div>
  #             </div>
  #           </div>
  #           <div class="actionGroup-root_left-saM actionGroup-root-1p7 "><button
  #               class=" button-root-16x button-root_size_base-Q7M  " type="submit">Check Warranty</button><a
  #               class=" button-root-16x button-root_size_base-Q7M  button-root_secondary-2MQ"
  #               href="/servicebench">ServiceBench®</a></div>
  #         </form>
  #         <h2 class="heading-h2-3Rs ">Serial Number: 1314A86771</h2>
  #         <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ table-root_zebraDark--yC  ">
  #           <tbody>
  #             <tr>
  #               <th>Name</th>
  #               <td>FAN COIL ALUM 3T</td>
  #             </tr>
  #             <tr>
  #               <th>Model Number</th>
  #               <td>
  #                 <div class="actionGroup-root_left-saM actionGroup-root-1p7 m-b-0"><span>FX4DNF037L00</span><a
  #                     class=" button-root-16x button-root_size_s-2cU  button-root_secondary-2MQ"
  #                     href="/part-finder/FX4DNF037L00">View Parts</a></div>
  #               </td>
  #             </tr>
  #             <tr>
  #               <th>Owner</th>
  #               <td> </td>
  #             </tr>
  #             <tr>
  #               <th>Equipment Installation Address</th>
  #               <td></td>
  #             </tr>
  #             <tr>
  #               <th>Date Installed</th>
  #               <td class="text-nowrap"></td>
  #             </tr>
  #           </tbody>
  #         </table>
  #         <h2 class="heading-h2-3Rs ">Entitlement Overview</h2>
  #         <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ table-root_zebraDark--yC  ">
  #           <tbody>
  #             <tr>
  #               <th>Discrete Model Number</th>
  #               <td>FX4DNF037L00ABAA</td>
  #             </tr>
  #             <tr>
  #               <th>Warranty Policy Code</th>
  #               <td>CP205</td>
  #             </tr>
  #             <tr>
  #               <th>Warranty Policy Description</th>
  #               <td>FOR SPECIFIC COVERAGE ON NON-REGISTERED UNITS INSTALLED IN OWNER OCCUPIED, NON-OWNER OCCUPIED AND
  #                 COMMERCIAL APPLICATIONS, REFER TO WARRANTY CERTIFICATE</td>
  #             </tr>
  #             <tr>
  #               <th>Standard Labor Warranty Expiration Date</th>
  #               <td></td>
  #             </tr>
  #             <tr>
  #               <th>Standard Part Warranty Expiration Date</th>
  #               <td></td>
  #             </tr>
  #             <tr>
  #               <th>UTC Property ID</th>
  #               <td></td>
  #             </tr>
  #             <tr>
  #               <th>Marked As</th>
  #               <td></td>
  #             </tr>
  #             <tr>
  #               <th>Shipped Date</th>
  #               <td class="text-nowrap">2014-04-04</td>
  #             </tr>
  #             <tr>
  #               <th>Replacement Of Model Number</th>
  #               <td></td>
  #             </tr>
  #             <tr>
  #               <th>Replacement Of Serial Number</th>
  #               <td></td>
  #             </tr>
  #           </tbody>
  #         </table>
  #         <h2 class="heading-h2-3Rs ">Warranty Info (All)</h2>
  #         <div class=" ">
  #           <div>
  #             <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ  table-root_zebraLight-11Q ">
  #               <thead>
  #                 <tr>
  #                   <th>Component Code</th>
  #                   <th>Warranty Length</th>
  #                   <th>Installed After</th>
  #                   <th>Application Type</th>
  #                   <th>Brand</th>
  #                 </tr>
  #               </thead>
  #               <tbody>
  #                 <tr>
  #                   <td>Standard Parts Warranty</td>
  #                   <td>5 years</td>
  #                   <td class="text-nowrap">2009-01-01</td>
  #                   <td>Owner Occupied Residential</td>
  #                   <td>ALL</td>
  #                 </tr>
  #                 <tr>
  #                   <td>Standard Parts Warranty</td>
  #                   <td>5 years</td>
  #                   <td class="text-nowrap">2012-01-01</td>
  #                   <td>Owner Occupied Residential</td>
  #                   <td>ALL</td>
  #                 </tr>
  #               </tbody>
  #             </table>
  #           </div>
  #         </div>
  #         <h2 class="heading-h2-3Rs ">Warranty Info (Original)</h2>
  #         <div class=" ">
  #           <div>
  #             <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ  table-root_zebraLight-11Q ">
  #               <thead>
  #                 <tr>
  #                   <th>Component Code</th>
  #                   <th>Warranty Length</th>
  #                   <th>Installed After</th>
  #                   <th>Application Type</th>
  #                   <th>Brand</th>
  #                 </tr>
  #               </thead>
  #               <tbody>
  #                 <tr>
  #                   <td>Standard Parts Warranty</td>
  #                   <td>5 years</td>
  #                   <td class="text-nowrap">2009-01-01</td>
  #                   <td>Owner Occupied Residential</td>
  #                   <td>ALL</td>
  #                 </tr>
  #               </tbody>
  #             </table>
  #           </div>
  #         </div>
  #         <h2 class="heading-h2-3Rs ">Warranty Info (Subsequent)</h2>
  #         <div class=" ">
  #           <div>
  #             <table class="table-root-jM5 table-root_border-JoY   table-root_hover-2xJ  table-root_zebraLight-11Q ">
  #               <thead>
  #                 <tr>
  #                   <th>Component Code</th>
  #                   <th>Warranty Length</th>
  #                   <th>Installed After</th>
  #                   <th>Application Type</th>
  #                   <th>Brand</th>
  #                 </tr>
  #               </thead>
  #               <tbody>
  #                 <tr>
  #                   <td>Standard Parts Warranty</td>
  #                   <td>5 years</td>
  #                   <td class="text-nowrap">2012-01-01</td>
  #                   <td>Owner Occupied Residential</td>
  #                   <td>ALL</td>
  #                 </tr>
  #               </tbody>
  #             </table>
  #           </div>
  #         </div>
  #       </div>
  #     </div>
  #   </div>
  # </main>'''

### start bs4 scrape
  #return html
  if html and html is not(None):
    #print(html)
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

      model_number = soup.select_one('th:-soup-contains("Discrete Model Number")').find_next('td')
      model_number = model_number.get_text().strip()
      if model_number:
        warranty_object["model_number"] = model_number
      else:
         model_number = soup.select_one('th:-soup-contains("Model Number")').find_next('td').find_next('span')
         warranty_object["model_number"] = model_number.get_text().strip()

      # GET OWNER NAME
      owner_name = soup.select_one('th:-soup-contains("Owner")').find_next('td')
      owner_name = owner_name.get_text().strip()
      if owner_name and owner_name is not(None):
        if owner_name.split()[1] == owner_last_name:
          warranty_object["last_name_match"] = True

      # GET INSTALL DATE
      install_date = soup.select_one('th:-soup-contains("Date Installed")').find_next('td')
      install_date = install_date.get_text().strip()
      if install_date and install_date is not(None):
        # 2022-11-03
        install_date = time.mktime(datetime.strptime(install_date, "%Y-%m-%d").timetuple())
        warranty_object["install_date"] = int(install_date)

      # GET SHIPPED DATE
      shipped_date = soup.select_one('th:-soup-contains("Shipped Date")').find_next('td')
      shipped_date = shipped_date.get_text().strip()
      if shipped_date and shipped_date is not(None):
        # 2022-11-03
        shipped_date = time.mktime(datetime.strptime(shipped_date, "%Y-%m-%d").timetuple())
        warranty_object["shipped_date"] = int(shipped_date)

      #print(warranty_object)

      # GET INDIVIDUAL WARRANTIES
      warranties = None
      if soup.select_one('h2:-soup-contains("Warranty Info (Original)")'):
        warranties = []
        warranty_table = soup.select_one('h2:-soup-contains("Warranty Info (Original)")').find_next('table')
        
        warranty_body = warranty_table.find("tbody")
        #print(warranty_body)
        rows = warranty_body.findAll('tr')
        #print(rows)
        if soup.select_one('th:-soup-contains("Warranty Start")'):
          #print("registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            #print(cols)
            # unwanted = cols[0].find('a')
            # unwanted.extract()
            warranty_details["name"] = cols[0].get_text().strip()
            #print(warranty_details)
            warranty_details["description"] = cols[1].get_text().strip()
            start_date = cols[3].get_text().strip()
            # 2022-11-03
            start_date = time.mktime(datetime.strptime(start_date, "%Y-%m-%d").timetuple())
            warranty_details["start_date"] = int(start_date)
            end_date = cols[4].get_text().strip()
            # 2022-11-03
            end_date = time.mktime(datetime.strptime(end_date, "%Y-%m-%d").timetuple())
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
          #print("no registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            warranty_details["name"] = cols[0].get_text().strip()
            warranty_details["description"] = cols[1].get_text().strip()
            warranty_details["type"] = "Standard"
            warranties.append(warranty_details)
          warranty_object["warranties"] = warranties
      elif soup.select_one('h2:-soup-contains("Warranty Info (All)")'):
        warranties = []
        warranty_table = soup.select_one('h2:-soup-contains("Warranty Info (All)")').find_next('table')
        
        warranty_body = warranty_table.find("tbody")
        #print(warranty_body)
        rows = warranty_body.findAll('tr')
        #print(rows)
        if soup.select_one('th:-soup-contains("Warranty Start")'):
          #print("registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            #print(cols)
            # unwanted = cols[0].find('a')
            # unwanted.extract()
            warranty_details["name"] = cols[0].get_text().strip()
            #print(warranty_details)
            warranty_details["description"] = cols[1].get_text().strip()
            start_date = cols[3].get_text().strip()
            # 2022-11-03
            start_date = time.mktime(datetime.strptime(start_date, "%Y-%m-%d").timetuple())
            warranty_details["start_date"] = int(start_date)
            end_date = cols[4].get_text().strip()
            # 2022-11-03
            end_date = time.mktime(datetime.strptime(end_date, "%Y-%m-%d").timetuple())
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
          #print("no registration")
          for tr in rows:
            warranty_details = {}
            cols = tr.findAll('td')
            warranty_details["name"] = cols[0].get_text().strip()
            warranty_details["description"] = cols[1].get_text().strip()
            warranty_details["type"] = "Standard"
            warranties.append(warranty_details)
          warranty_object["warranties"] = warranties
      
        
    else:
     warranty_object = None
  else:
     warranty_object = None

  #pdf = None
  print(warranty_object)   
  encoded_pdf = None
  if pdf is not(None):
    with open(pdf.name, "rb") as pdf:
      encoded_pdf = base64.b64encode(pdf.read())

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

## GET TRANE WARRANTY
@app.task
def getTraneWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  
  print(f"### Starting Trane Warranty Lookup: {serial_number}")

  dotenv.load_dotenv()

  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
      text = None
      download = None
      browser = playwright.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      page.goto("https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
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
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
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

        #pdf = pdfplumber.open(pdf)
        reader = pdfplumber.open(temp_file)
        #reader = PdfReader(pdf)
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

  
  if result is not(None):
   
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
    
    llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
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

    ### Build chain to structure raw text from trane pdf
    llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
    chain = create_extraction_chain_pydantic(pydantic_schema=Properties, llm=llm)
    trane_warranty = chain.run(output)
    #print(lennox_warranty)

    trane_warranty = json.dumps([warranty.__dict__ for warranty in trane_warranty])
    #lennox_warranty = json.dumps(lennox_warranty.__dict__)
    #print(lennox_warranty)

    trane_warranty = json.loads(trane_warranty)
    #print(lennox_warranty)

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
      #print(html)
      if "Congratulations, your Limited Warranty registration was successfully submitted" in str(html):
        warranty_object["last_name_match"] = True
      print(trane_warranty)
      warranties = [obj for obj in trane_warranty if obj['serial_number'] == serial_number] 
      for warranty in warranties:
        #06/22/2014
        end_date = warranty["end_date"]
        end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)

        term = warranty["term"]
        years = re.search(r"\d+", term).group()
        #print(int(years))
        years = int(years)
        #print(int(end_date))
        start_date = (datetime.fromtimestamp(end_date) - relativedelta(years=years)).strftime("%m/%d/%Y")
        # 2021-04-01T00:00:00
        start_date = time.mktime(datetime.strptime(start_date, "%m/%d/%Y").timetuple())
        warranty["start_date"] = int(start_date)
        warranty_object["install_date"] = int(start_date)
        warranty_object["register_date"] = int(start_date)
        warranty_object["model_number"] = warranty["model_number"]
        warranty["name"] = warranty["part"].title()

        del warranty["part"]
        del warranty["term"]
        del warranty["model_number"]
        del warranty["serial_number"]
        #delattr(warranty, "parts")
        #delattr(warranty, "term")

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
      encoded_pdf = base64.b64encode(pdf.read())

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)


## GET York WARRANTY
@app.task
def getYorkWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  
  print(f"### Starting York Warranty Lookup: {serial_number}")

  dotenv.load_dotenv()
  
  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
      html = None
      download = None
      pdf = None
      browser = playwright.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      page.goto("https://www.yorknow.com/warranty-tools")
      page.query_selector("#warrantysearch").click()
      page.query_selector("#warrantysearch").fill(serial_number)
      #print(page.query_selector("#warrantysearch"))
      #print(page.get_by_role("button", name="Lookup Warranty"))
      page.get_by_role("button", name="Lookup Warranty").click()
      time.sleep(10)
      #print(page.query_selector(".details-title"))
      page.query_selector(".details-title").click()
      html = page.query_selector("#warranty-details").inner_html()
      try:
        with page.expect_download() as download_info:
          page.get_by_role('button', name='Download Warranty Certificate').click()
        download = download_info.value
      except Exception as e:
        print(f"something went wrong: {e}")
      
      if download is not(None):

        temp_file = NamedTemporaryFile(delete=True)
        download.save_as(temp_file.name)
        temp_file.flush()

        # ---------------------
        context.close()
        browser.close()
        return {"html": html, "pdf": temp_file.file}
      else:
        context.close()
        browser.close()
        return None

  with sync_playwright() as playwright:
    result = run(playwright)
    html = result["html"]
    pdf = result["pdf"]

  soup = BeautifulSoup(html, "html.parser")

  if soup.select_one('div:-soup-contains("Warranty Unit Details")'):

    warranty_object = {}
    warranty_object["is_registered"] = False
    warranty_object["shipped_date"] = None
    warranty_object["install_date"] = None
    warranty_object["register_date"] = None
    warranty_object["manufacture_date"] = None
    warranty_object["last_name_match"] = False
    warranty_object["certificate"] = None

    # GET MODEL NUMBER
    warranty_unit_details = soup.select_one(".details-content-row")
    #print(warranty_unit_details)
    rows = warranty_unit_details.findAll('div')
    #print(rows)
    model_number = rows[1].get_text().strip()
    print(f"model number: {model_number}")
    warranty_object["model_number"] = model_number

    # GET REGISTER STATUS
    register_status = rows[3].get_text().strip()
    if register_status == "Product registered":
      warranty_object["is_registered"] = True

    # GET INSTALL DATE
    latest_date = soup.find('div', text = "Latest Date On Record:").find_next('div')
    #print(latest_date)
    latest_date = latest_date.get_text().strip()
    #print(latest_date)
    latest_date = time.mktime(datetime.strptime(latest_date, "%m/%d/%Y").timetuple())
    print(f"latest date: {latest_date}")
    warranty_object["install_date"] = int(latest_date)

    # GET INDIVIDUAL WARRANTIES
    warranties = []
    warranty_table = soup.select_one("#warranty-coverage-table")
    print(warranty_table)
    warranty_rows = warranty_table.findAll("div", class_="details-content-row")
    print(warranty_rows)
    for warranty_row in warranty_rows:
      print(warranty_row)
      warranty_details = {}
      warranty_fields = warranty_row.findAll('div')
      name = warranty_fields[0].get_text().strip()
      warranty_details["name"] = name

      end_date = warranty_fields[2].get_text().strip()
      end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
      warranty_details["end_date"] = int(end_date)
      warranty_details["start_date"] = int(latest_date)
      warranty_details["type"] = "Standard"
      warranties.append(warranty_details)
    warranty_object["warranties"] = warranties

  else:
    warranty_object = None
  
  print(warranty_object)
  encoded_pdf = None
  if pdf is not(None):
    with open(pdf.name, "rb") as pdf:
      encoded_pdf = base64.b64encode(pdf.read())

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)


## GET LENNOX WARRANTY
@app.task
def getLennoxWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  
  print(f"### Starting Lennox Warranty Lookup: {serial_number}")

  dotenv.load_dotenv()
  LENNOX_EMAIL = os.environ.get("LENNOX_EMAIL")
  LENNOX_PASSWORD = os.environ.get("LENNOX_PASSWORD")

  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
      text = None
      download = None
      html = None
      browser = playwright.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      print("going to page")
      page.goto("https://www.lennoxpros.com/")
      print("starting sign in")
      page.get_by_role("link", name="Sign In", exact=True).click()
      page.get_by_placeholder("Email Address").click()
      page.get_by_placeholder("Email Address").fill(LENNOX_EMAIL)
      page.get_by_placeholder("Password").click()
      page.get_by_placeholder("Password").fill(LENNOX_PASSWORD)
      page.get_by_label("Sign In", exact=True).click()
      print("navigating to warranty")
      page.get_by_role("link", name="Warranty").first.click()
      page.get_by_role("link", name="Warranty Registration Certificate Lookup").click()
      print("starting to fill form")
      page.get_by_label("Equipment Owner Last Name*").click()
      page.get_by_label("Equipment Owner Last Name*").fill(owner_last_name)
      page.get_by_label("Serial Number or Registration Number*").click()
      page.get_by_label("Serial Number or Registration Number*").fill(serial_number)
      page.get_by_role("button", name="Search").click()
      print(owner_last_name)
      print(serial_number)
      print("searching for serial number")
      try:
        page.locator("#warrantyLookUpTable").click()
        print("found lookup table")
        time.sleep(5)
        print(page.get_by_role("link", name="Print"))
        with page.expect_download() as download_info:
          page.get_by_role("link", name="Print").click()
        download = download_info.value
      except Exception as e:
        print(f"something went wrong: {e}")
        try:
          print("trying quick coverage tool")
          page.get_by_role("link", name="Quick Coverage Lookup Tool").click()
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


      # # page.get_by_label("Serial Number or Registration Number*").fill("1923H50626")
      # # page.get_by_label("Equipment Owner Last Name*").click()
      # # page.get_by_label("Equipment Owner Last Name*").fill("Nevarez")
      # page.get_by_role("button", name="Search").click()
      # page.get_by_role("cell", name="Registration Number").click()
      # page.get_by_role("cell", name="Registration Number").click()
      # try:
      #   with page.expect_download() as download_info:
      #     page.get_by_role("link", name="Print").click()
      #   download = download_info.value
      # except Exception as e:
      #   print(f"something went wrong: {e}")
      # # with page.expect_popup() as page1_info:
      # #     page.get_by_role("link", name="Print").click()
      # # page1 = page1_info.value
      # # page.get_by_label("Equipment Owner Last Name*").click()
      
      texts = ""
      if download is not(None):
        temp_file = NamedTemporaryFile(delete=True)
        download.save_as(temp_file.name)
        temp_file.flush()

        #pdf = pdfplumber.open(pdf)
        reader = pdfplumber.open(temp_file)
        #reader = PdfReader(pdf)
        texts = ""
        for page in reader.pages:
          text = page.extract_text()
          texts += text

        # ---------------------
        context.close()
        browser.close()
        return {"text": texts, "pdf": temp_file.file, "html": None}
      elif html is not(None):
        return {"text": None, "pdf": None, "html": html}
      else:
        context.close()
        browser.close()
        return None


  text = None
  pdf = None
  html = None
  with sync_playwright() as playwright:
      result = run(playwright)
      if result is not(None):
        text = result["text"]
        pdf = result["pdf"]
        html = result["html"]

  
  if result is not(None):

    if html is not(None):
      # return html
    
#       html = '''
#       <table width="70%">
#   <tbody>
#     <tr align="left">
#       <td colspan="2">
#         <h4>The warranty information for the product/part you entered is shown below:</h4>
#         <br>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Serial Number: </b>
#       </td>
#       <td>
#         <span id="lblSerialNumber">1923H50626</span>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Model Number: </b>
#       </td>
#       <td>
#         <span id="lblModelNumber">ML17XC1-059-230A02</span>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Installation Date: </b>
#       </td>
#       <td>
#         <span id="lblInsDate">09/13/2023</span>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Lennox Limited Parts Warranty: </b>
#       </td>
#       <td>
#         <span id="lblStandardWarranty">5 Years </span>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%;">
#         <b>Lennox Extended Parts Warranty: </b>
#       </td>
#       <td>
#         <span id="lblExtendedWarranty">Not Available</span>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Extended Parts Warranty Expiration: </b>
#       </td>
#       <td>
#         <span id="lblWarrantyExpiration">Not Available</span>
#       </td>
#     </tr>
#     <tr id="TableLNX1" align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Lennox Limited Labor Warranty: </b>
#       </td>
#       <td>
#         <span id="lblStandardLaborWarranty">Not Available</span>
#       </td>
#     </tr>
#     <tr id="TableLNX2" align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Lennox Limited Labor Expiration: </b>
#       </td>
#       <td>
#         <span id="lblStandardLaborExpiration">Not Available</span>
#       </td>
#     </tr>
#     <tr align="left" valign="top">
#       <td style="height: 35px; width: 25%">
#         <b>Note: </b>
#       </td>
#       <td>
#         <span id="lblNote">This information is provided as a good faith estimate of the Manufacturer's Warranty coverage
#           based on the data available at the time of look-up. Information provided by this system is not intended to
#           replace or alter the terms or conditions of warranty coverage laid out in the Lennox Equipment Limited
#           Warranty Certificate provided with the unit at the time of purchase.</span>
#       </td>
#     </tr>
#   </tbody>
# </table>
#       '''
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
      if install_date and install_date is not(None) and "Not Available" not in install_date:
        # 09/13/2023
        install_date = time.mktime(datetime.strptime(install_date, "%m/%d/%Y").timetuple())
        warranty_object["install_date"] = int(install_date)
        warranty_object["is_registered"] = True
      else:
        install_date = None

      # GET WARRANTIES
      
      # GET STANDARD PARTS WARRANTY
      standard_parts_warranty_term = soup.select_one("#lblStandardWarranty").get_text().strip()
      if "Not Available" not in str(standard_parts_warranty_term) and install_date:

        warranties = []
        warranty = {}

        warranty["start_date"] = int(install_date)

        term = standard_parts_warranty_term
        years = re.search(r"\d+", term).group()
        #print(int(years))
        years = int(years)
        #print(int(end_date))
        end_date = (datetime.fromtimestamp(install_date) + relativedelta(years=years)).strftime("%m/%d/%Y")
        # 2021-04-01T00:00:00
        end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
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
      extended_parts_warranty_end_date = soup.select_one("#lblWarrantyExpiration").get_text().strip()
      if "Not Available" not in str(extended_parts_warranty_end_date) and install_date:
        warranty = {}

        warranty["start_date"] = int(install_date)

        end_date = extended_parts_warranty_end_date
        end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)
        warranty["name"] = "Parts"
        warranty["type"] = "Extended"
        warranties.append(warranty)

      # GET STANDARD LABORY WARRANTY
      standard_labor_warranty_end_date = soup.select_one("#lblStandardLaborExpiration").get_text().strip()
      if "Not Available" not in str(standard_labor_warranty_end_date) and install_date:

        warranty = {}

        warranty["start_date"] = int(install_date)

        end_date = standard_labor_warranty_end_date
        end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
        warranty["end_date"] = int(end_date)
        warranty["name"] = "Labor"
        warranty["type"] = "Standard"
        warranties.append(warranty)
      

      warranty_object["warranties"] = warranties

    if text is not(None):
      
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
      
      llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
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
      ### Build chain to structure raw text from trane pdf
      print("starting pydantic")
      llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      try:
        chain = create_extraction_chain_pydantic(pydantic_schema=Property, llm=llm)
        lennox_warranty = chain.run(output)
        print(lennox_warranty)
      except Exception as e:
          print(f"something went wrong {e}")
          print("trying new parse")
          try:
            chain = create_extraction_chain_pydantic(pydantic_schema=Properties, llm=llm)
            lennox_warranty = chain.run(output)
            lennox_warranty = lennox_warranty[0].property
            print(lennox_warranty)
          except Exception as e:
            print(f"something went wrong {e}")
     

      lennox_warranty = json.dumps([warranty.__dict__ for warranty in lennox_warranty])
      #lennox_warranty = json.dumps(lennox_warranty.__dict__)
      print(lennox_warranty)

      lennox_warranty = json.loads(lennox_warranty)
      #print(lennox_warranty)

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
        #print(html)

        #print("here first")
        warranties = [obj for obj in lennox_warranty if obj['serial_number'] == serial_number] 
        for warranty in warranties:
          #06/22/2014
          end_date = warranty["parts_warranty_expiration"]
          end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
          warranty["end_date"] = int(end_date)

          #06/22/2014
          start_date = warranty["installation_date"]
          start_date = time.mktime(datetime.strptime(start_date, "%m/%d/%Y").timetuple())
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
            #06/22/2014
            end_date = warranty["labor_expiration"]
            end_date = time.mktime(datetime.strptime(end_date, "%m/%d/%Y").timetuple())
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

          #delattr(warranty, "parts")
          #delattr(warranty, "term")

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
  if pdf is not(None):
    with open(pdf.name, "rb") as pdf:
        encoded_pdf = base64.b64encode(pdf.read())

  if int(instant) == 1:
    return {"warranty_object": warranty_object, "filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_scan_id": equipment_scan_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": json.dumps(warranty_object), "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)


## FIND EQUIPMENT MANUALS
@app.task
def manual_lookup(model_number, manufacturer, equipment_type, model_id):
  dotenv.load_dotenv()

  return model_number


## GET GOODMAN WARRANTY
@app.task
def getGoodmanWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  
  print(f"### Starting Goodman Warranty Lookup: {serial_number}")

  dotenv.load_dotenv()

  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
      text = None
      download = None
      browser = playwright.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      page.goto("https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
      time.sleep(5)
      page.locator("input[name=\"serialNo\"]").click()
      page.locator("input[name=\"serialNo\"]").fill(serial_number)
      page.locator("input[name=\"lastName\"]").click()
      page.locator("input[name=\"lastName\"]").fill(owner_last_name)
      page.get_by_role("button", name="Search").click()
      time.sleep(5)
      try:
        with page.expect_download() as download_info:
          page.get_by_role("button", name="Search").click()
        download = download_info.value
      except Exception as e:
        print(f"something went wrong: {e}")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://warrantylookup.tranetechnologies.com/wrApp/index.html#/trane/search")
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
      
      if download is not(None):
        temp_file = NamedTemporaryFile(delete=True)
        download.save_as(temp_file.name)
        temp_file.flush()

        # ---------------------
        context.close()
        browser.close()
        return {"text": None, "pdf": temp_file.file}

      context.close()
      browser.close()
      return None
      

  pdf = None
  with sync_playwright() as playwright:
      result = run(playwright)
      if result is not(None):
        pdf = result["pdf"]
  
  encoded_pdf = None
  if pdf is not(None):
    with open(pdf.name, "rb") as pdf:
        encoded_pdf = base64.b64encode(pdf.read())

  if int(instant) == 1:
    return {"filedata": encoded_pdf}

  else:
    if equipment_scan_id and equipment_scan_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": None, "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)

    if equipment_id and equipment_id is not(None):
      r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/update_warranty_data', data={"warranty_object": None, "equipment_id": equipment_id, "filedata": encoded_pdf}, timeout=30)
      print(r)



## GET AO SMITH WARRANTY
@app.task
def getAOSmithWarranty(serial_number, instant, equipment_scan_id, equipment_id, owner_last_name):
  
  print(f"### Starting AO Smith Warranty Lookup: {serial_number}")

  dotenv.load_dotenv()

  from playwright.sync_api import Playwright, sync_playwright, expect

  def run(playwright: Playwright) -> None:
      text = None
      download = None
      browser = playwright.chromium.launch(headless=True)
      context = browser.new_context()
      page = context.new_page()
      page.goto("https://www.hotwater.com/support/warranty-verification.html")
      time.sleep(5)
      page.frame_locator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').click()
      page.frame_locator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').fill(serial_number)
      page.frame_locator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_btnSearch').click()
      try:
        page.frame_locator('iframe[title="Warranty Verification"]').get_by_role('heading', name='Unit Details').click()
      except Exception as e:
        print(f"something went wrong: {e}")
        

#       import { test, expect } from '@playwright/test';

# test('test', async ({ page }) => {
#   await page.goto('https://www.hotwater.com/support/warranty-verification.html');
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').fill('2041121325917');
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_btnSearch').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').getByText('Serial Check Results Unit').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').getByRole('heading', { name: 'Unit Details' }).click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').click({
#     clickCount: 3
#   });
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').press('Meta+Shift+ArrowLeft');
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_txtSerial').fill('9211678005');
#   await page.frameLocator('iframe[title="Warranty Verification"]').locator('#MainContent_SerialDetails_btnSearch').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').getByText('Nothing found. If you require').click();
#   await page.frameLocator('iframe[title="Warranty Verification"]').getByText('Nothing found. If you require').click();
# });



## FIND EQUIPMENT MANUALS
@app.task
def manual_lookup(model_number, manufacturer, equipment_type, model_id):
  dotenv.load_dotenv()
  return model_number

@app.task
def test_task():
  print("TEST_TASK STARTING")
  sleep(5)
  print("TEST_TASK COMPLETED")
  return time.time()

@app.task
def sum_test_task(a, b):
  sleep(5)
  print("sum test task completed")
  return a + b
