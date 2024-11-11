import time
import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.callbacks import get_openai_callback
from langchain.chains import create_extraction_chain
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_loaders import OnlinePDFLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.prompts import PromptTemplate
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.utilities import SerpAPIWrapper
from serpapi.google_search import GoogleSearch
from urllib.parse import urlparse
from utils import search_and_parse_pdfs


from celery_app import celery_app


@celery_app.task
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

    load_dotenv()

    # Create return variables for resource urls and related model numbers
    potential_resources = []
    resource_urls = []
    related_models = []
    bad_urls = []

    # model_number = "22V50F1"
    print(f"*** Starting new model search: {model_number}")

    # Setup SerpAPI Tool
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
        if not (search_results.get("error")):
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
      headers = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
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

        # loader = SeleniumURLLoader([url])
        # loader = PlaywrightURLLoader(urls=[url])
        loader = AsyncChromiumLoader([url])
        # loader = AsyncHtmlLoader([url])

        print("starting to load html")
        html = loader.load()
        print("waiting...")
        time.sleep(10)
        # extract pdfs
        scrape_html = html
        # print(f"here is the html: {scrape_html}")
        print(f"checking to see if list")
        if isinstance(scrape_html, list):
          print(f"is list")
          scrape_html = next(iter(scrape_html))
        if scrape_html:
          print(f"getting page content to scrape")
          scrape_html = scrape_html.page_content
          sopa = BeautifulSoup(scrape_html, "html.parser")
          # print(f"all links: {sopa.find_all('a')}")
          counter = 0
          for link in sopa.find_all('a'):
            current_link = link.get('href')
            current_text = link.text
            if current_link:
              # print(f"current link: {current_link}")
              if current_link.endswith('pdf') or "pdf" in current_text:
                if not (urlparse(current_link).hostname):
                  potential_resources.append(
                      "https://" + hostname + current_link)
                  counter += 1
                else:
                  potential_resources.append(current_link)
                  counter += 1
            if counter >= 7:
              break

        # print(potential_resources)

        bs_transformer = BeautifulSoupTransformer()
        print("starting to parse html elements")
        docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=[
                                                              "span", "p", "ul", "li", "h1", "h2", "h3", "h4", "dl", "dt", "tr"])
        # Grab the first 1000 tokens of the site
        # print(f"here are the docs: {docs_transformed}")

        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=3500,
                                                                        chunk_overlap=100)
        print("starting to split documents")
        # print(f"here is the docs: {docs_transformed}")
        splits = splitter.split_documents(docs_transformed)
        print("done splitting")
        # print(f"here are the splits: {splits}")
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
          # continue

      print(f"length of pdf is {len(pdf_pages)} pages")

      if len(pdf_pages) >= 1:
        potential_resources.append(url)
        # Get full pdf in text
        text = ''
        for page in pdf_pages:
          text += page.page_content

        print("starting split")

        # Split text to limit tokens passed to LLM
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=3500,
            chunk_overlap=200,
            length_function=len,
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
    r = requests.get(
        'https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/equipmentiq_types', timeout=30).json()
    for type in r:
      equipment_types.append(type["name"])

    # Get equipment manufacturers from database
    equipment_manufacturers = []
    r = requests.get(
        'https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/equipmentiq_manufacturers', timeout=30).json()
    for manufacturer in r:
      equipment_manufacturers.append(manufacturer["name"])

    # print(equipment_manufacturers)

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
      search_results = serp_api_search(
          f"{model_number} {supporting_data}")
      if search_results:
        for search_result in search_results:
          urls.append({"url": search_result["link"]})
      else:
        urls = []

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

    base_equipment_info_search_prompt = PromptTemplate(
        input_variables=["model_number", "supporting_data",
                         "text", "equipment_types", "equipment_manufacturers"],
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
      # url = "https://www.ferguson.com/product/american-standard-hvac-4wcc3-series-5-ton-13-seer-convertible-r-410a-packaged-heat-pump-a4wcc3060a1000a/2757673.html"
      # url = "https://python.langchain.com/docs/use_cases/web_scraping"
      # text = parse_url(url)

    print(f"here is the text: {texts}")
    # Create agent for internet web search
    llm = AzureChatOpenAI(deployment_name="gpt35turbo16k",
                          model_name="gpt-35-turbo-16k", temperature=0)
    # prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
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

    # Build chain to structure raw text from internet search
    llm = AzureChatOpenAI(deployment_name="gpt35turbo",
                          model_name="gpt-35-turbo", temperature=0)
    chain = create_extraction_chain(schema, llm)
    messages = [{"role": "user", "content": output}]
    model_object = chain.run(messages)
    print(model_object)
    if isinstance(model_object, list):
      model_object = next(iter(model_object))

    # IF AC

    if model_object.get("equipment_type") == "1" or model_object.get("equipment_type") == "13" or model_object.get("equipment_type") == "14" or model_object.get("equipment_type") == "16" or model_object.get("equipment_type") == "17" or model_object.get("equipment_type") == "18" or model_object.get("equipment_type") == "22" or model_object.get("equipment_type") == "38" or model_object.get("equipment_type") == "39":
      ac_search_prompt = PromptTemplate(
          input_variables=["model_number",
                           "equipment_type", "manufacturer", "text"],
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

      # Create agent for internet web search
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
      # prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
      chain = LLMChain(llm=llm, prompt=ac_search_prompt)
      output = chain.run({
          'model_number': model_object.get("model_number"),
          'manufacturer': model_object.get("manufacturer"),
          'equipment_type': model_object.get("equipment_type"),
          'text': texts
      })

      # Set schema to structure internet search data in JSON
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

      # Build chain to structure raw text from internet search
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = create_extraction_chain(schema, llm)
      messages = [{"role": "user", "content": output}]
      ac_object = chain.run(messages)

      # Get first object returned by extraction chain
      if isinstance(ac_object, list):
        ac_object = next(iter(ac_object))
      print(ac_object)
      model_object.update(ac_object)
      print(f'''*** Here is structured data for AC: {model_number}:
              {model_object}
              ''')

    # IF WH

    elif model_object.get("equipment_type") == "3":

      print("water heater")
      wh_search_prompt = PromptTemplate(
          input_variables=["model_number",
                           "equipment_type", "manufacturer", "text"],
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
      # Create agent for internet search task
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
      # prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
      chain = LLMChain(llm=llm, prompt=wh_search_prompt)
      output = chain.run({
          'model_number': model_object.get("model_number"),
          'manufacturer': model_object.get("manufacturer"),
          'equipment_type': model_object.get("equipment_type"),
          'text': texts
      })

      # return output

      # Set schema to structure internet search data in JSON
      schema = {
          "properties": {
              "water_heater_btus": {"type": "integer"},
              "water_heater_gallons": {"type": "string"},
              "water_heater_type": {"type": "string"},
              "water_heater_fuel": {"type": "string"},
          }
      }

      # Build chain to structure raw text from internet search
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = create_extraction_chain(schema, llm)
      messages = [{"role": "user", "content": output}]
      wh_object = chain.run(messages)
      # print(wh_object)

      # Get first object returned by extraction chain
      if isinstance(wh_object, list):
        wh_object = next(iter(wh_object))
      # print(wh_object)
      model_object.update(wh_object)
      print(f'''*** Here is structured data for WH: {model_number}:
                {model_object}
                ''')

      # IF Furnace

    elif model_object.get("equipment_type") == "2":
      print("furnace")
      fur_search_prompt = PromptTemplate(
          input_variables=["model_number",
                           "equipment_type", "manufacturer", "text"],
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

      # Create agent for internet search task
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo16k", model_name="gpt-35-turbo-16k", temperature=0)
      # prompt = base_equipment_info_search_prompt.format(model_number=model_number, supporting_data=supporting_data, text=parsed_url)
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

      # Set schema to structure internet search data in JSON
      schema = {
          "properties": {
              "furnace_btus": {"type": "integer"},
              "furnace_tonnage": {"type": "string"},
              "furnace_afue": {"type": "integer"},
              "furnace_voltage": {"type": "string"},
              "furnace_fuel": {"type": "string"},
          }
      }

      # Build chain to structure raw text from internet search
      llm = AzureChatOpenAI(
          deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
      chain = create_extraction_chain(schema, llm)
      messages = [{"role": "user", "content": output}]
      fur_object = chain.run(messages)
      # print(fur_object)

      # Get first object returned by extraction chain
      if isinstance(fur_object, list):
        fur_object = next(iter(fur_object))
      # print(wh_object)
      model_object.update(fur_object)
      print(f'''*** Here is structured data for FUR: {model_number}:
                {model_object}
                ''')

    # END Internet Search Process

    # START PDF Search process

    # Only run if model has been marked as verified
    if not (model_object.get("model_number") == None) and not (model_object.get("manufacturer") == None) and not (model_object.get("equipment_type") == None):
      # print(model_object)

      # Setup SERP API Tool for product data pdf search
      params = {
          "q": f"{model_number} product data pdf",
          "hl": "en",
          "gl": "us",
          "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
      }
      pdf_search = GoogleSearch(params)

      # Run pdf search
      results = pdf_search.get_dict()
      # print(results['organic_results'])

      # print(results)

      if not (results.get("error")):
        if results.get('organic_results'):
          results = results['organic_results']

        print("start pdfs")
        print(f"potential resources: {potential_resources}")
        search_results = search_and_parse_pdfs(
            results, model_number, resource_urls, related_models, potential_resources, bad_urls)
        print("done")
      else:
        print("no search results")

      if not (any(url['type'] == "Installation Manual" for url in resource_urls)):
        params = {
            "q": f"{model_number} install manual pdf",
            "hl": "en",
            "gl": "us",
            "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
        }
        pdf_search = GoogleSearch(params)

        # Run pdf search
        results = pdf_search.get_dict()
        # print(results['organic_results'])

        if not (results.get("error")):
          if results.get('organic_results'):
            results = results['organic_results']

          print("start install manual pdfs")
          print(f"bad urls: {bad_urls}")
          search_results = search_and_parse_pdfs(
              results, model_number, resource_urls, related_models, [], bad_urls)
          print("done")
        else:
          print("no search results")

      if not (any(url['type'] == "Owners Manual" for url in resource_urls)):
        params = {
            "q": f"{model_number} owners manual pdf",
            "hl": "en",
            "gl": "us",
            "api_key": f"{os.getenv('SERPAPI_API_KEY')}"
        }
        pdf_search = GoogleSearch(params)

        # Run pdf search
        results = pdf_search.get_dict()
        # print(results['organic_results'])

        if not (results.get("error")):
          if results.get('organic_results'):
            results = results['organic_results']

          print("start owners manual pdfs")
          search_results = search_and_parse_pdfs(
              results, model_number, resource_urls, related_models, [], bad_urls)
          print("done last")
        else:
          print("no search results")

      # remove duplicate resources
      if resource_urls:
        unique_resources = [resource_urls[0]]
        for resource in resource_urls:
          if resource not in unique_resources:
            unique_resources.append(resource)

        resource_urls = unique_resources

      # remove duplicate related_models
      if related_models:
        unique_related_models = [related_models[0]]
        for model in related_models:
          if model not in unique_related_models:
            unique_related_models.append(model.strip())

        related_models = unique_related_models

      # set pdf manual variables
      product_data = next(
          (url for url in resource_urls if url['type'] == "Product Data"), None)
      if product_data is not (None):
        model_object["product_data"] = product_data["url"]

      iom = next(
          (url for url in resource_urls if url['type'] == "Installation Manual"), None)
      if iom is not (None):
        model_object["iom"] = iom["url"]

      owners_manual = next(
          (url for url in resource_urls if url['type'] == "Owners Manual"), None)
      if owners_manual is not (None):
        model_object["owners_manual"] = owners_manual["url"]

      service_manual = next(
          (url for url in resource_urls if url['type'] == "Service Manual"), None)
      if service_manual is not (None):
        model_object["service_manual"] = service_manual["url"]

      wiring_diagram = next(
          (url for url in resource_urls if url['type'] == "Wiring Diagram"), None)
      if wiring_diagram is not (None):
        model_object["wiring_diagram"] = wiring_diagram["url"]

      specs = next(
          (url for url in resource_urls if url['type'] == "Equipment Specs"), None)
      if specs is not (None):
        model_object["specs"] = specs["url"]

      model_object["resources"] = resource_urls
      model_object["related_models"] = related_models

      print(model_object)

    else:
      print("error")

    model_object["openai_data"] = {"total_tokens": cb.total_tokens, "prompt_tokens": cb.prompt_tokens,
                                   "completion_tokens": cb.completion_tokens, "total_cost": cb.total_cost}
    r = requests.post('https://x6fl-8ass-7cr7.n7.xano.io/api:CHGuzb789/equipmentiq_upload_new_model',
                      json={"model_object": model_object}, timeout=30)
    print(
        f"Status Code: {r.status_code}, Response: {r.json()}, Model: {model_object}")
    print(f"Model: {model_object}")
    print(f"Total Tokens: {cb.total_tokens}")
    print(f"Prompt Tokens: {cb.prompt_tokens}")
    print(f"Completion Tokens: {cb.completion_tokens}")
    print(f"Total Cost (USD): ${cb.total_cost}")
    return model_object
