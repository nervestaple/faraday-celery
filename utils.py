import requests
from langchain.prompts import PromptTemplate
from langchain.chains import create_extraction_chain
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.document_loaders import OnlinePDFLoader


### Iterate over pdfs returned in organic search results to see if they're relevant to the model number provided and what type of document it is
def search_and_parse_pdfs(organic_search_results, model_number, resource_urls, related_models, potential_resources, bad_urls):
  bad_pdf = 0
  for value in organic_search_results[0:3]:
    potential_resources.append(value['link'])

  if potential_resources:
    unique_potential_resources = []
    for resource in potential_resources:
      if resource not in unique_potential_resources and resource not in bad_urls and not any(resource_url.get('url') == resource for resource_url in resource_urls):
          unique_potential_resources.append(resource)

  potential_resources = unique_potential_resources



  for value in potential_resources:
    print(f"*** Bad pdf count: {bad_pdf}")

    if bad_pdf > 3:break
    
    ### Get link to pdf from search results
    new_link = value
    print(f"**** Checking {new_link} for pdf")

    ### Make sure link returns 200

    try:
        print("checking to see if valid url")
        r = requests.get(new_link, timeout=30)
        print(f"response was:{r}")
    except Exception as e:
        print(f"not valid pdf: {e}")
        bad_pdf += 1
        bad_urls.append(new_link)
    else:
      if r.status_code == 200 and (r.headers.get('content-type') == 'application/pdf' or r.headers.get('content-type') == 'application/octet-stream'):
        try:
            print("loading pdf")
            pdf_loader = PyPDFLoader(new_link)
        except Exception:
            print("bad request")
            bad_pdf += 1
            bad_urls.append(new_link)
        else:
            ### Load PDF and split into pages
            #pdf_loader = PyPDFLoader(new_link)
            try:
              print("load and split")
              pdf_pages = pdf_loader.load_and_split()
            except Exception as e:
              print(f"something bad happended: {e}")
              try:
                print("trying a different loader")
                loader = OnlinePDFLoader(new_link)
                pdf_pages = loader.load()
              except Exception as e:
                print(f"something bad happended: {e}")
                bad_pdf += 1
                bad_urls.append(new_link)
                continue  

            print(f"length of pdf is {len(pdf_pages)} pages")

            if len(pdf_pages) >= 1:
              ### Get full pdf in text
              text=''
              for page in pdf_pages:
                  text += page.page_content
              #print(text)
            else:
              bad_pdf += 1
              bad_urls.append(new_link)
              continue

            print("starting split")

            ### Split text to limit tokens passed to LLM
            text_splitter = CharacterTextSplitter(
                separator = "\n",
                chunk_size = 2500,
                chunk_overlap  = 200,
                length_function = len,
            )
            texts = text_splitter.split_text(text)

            if isinstance(texts, list):
              texts = next(iter(texts))
            #print(texts)

            ### Set params to determine if pdf is useful
            related = False
            document_type = None

            #model_number="DGAPAXX1625"
            #print(model_number)

            ### Set prommpt to parse pdf and determine if it's related to model and the type of pdf
            pdf_prompt = PromptTemplate(
                input_variables=["model_number", "pdf_data"],
                template='''Using the data below. Determine three things:
                - related (does this document reference the model number below or model numbers that start with the same 5 characters? If so, return true, if not return false)
                - document type (what type of document is this? Use the list of document types below to determine. If you can't determine the document type from the list below, return None)
                - other models (A list of other model numbers from the document that are similar to the model number below)

                document types:
                - Product Data (also known as Performance Data or Product Specifications)
                - Service Manual (also known as Technical Manual)
                - Installation Manual
                - Owners Manual
                - Wiring Diagram
                - Equipment Specs (also known as Specifciation Sheet)
                - Service Bulletin
                - Service Facts
                - Repair Parts (also known as Parts List or Replacement Parts)

                model number: {model_number}

                data: {pdf_data}
                '''
            )

            ### Setup chain to run pdf search
            llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
            chain = LLMChain(llm=llm, prompt=pdf_prompt)

            print("checking to see if pdf is relevant")
            try:
              ### Run chain to determine if PDF is useful
              output = chain.run({
                'model_number': model_number,
                'pdf_data': texts
                })
              print(output)
            except Exception as e:
              print(f"something bad happend: {e}")
            else:
              ### Setup schema to structure pdf search results
              schema = {
                  "properties": {
                      "related": {"type": "boolean"},
                      "document_type": {"type": "string"},
                      "other_models": {"type": "string"},                    
                  },
                  "required": ["related", "document_type"],
              }

              ### Setup chain to structure pdf search results
              llm = AzureChatOpenAI(deployment_name="gpt35turbo", model_name="gpt-35-turbo", temperature=0)
              chain = create_extraction_chain(schema, llm)

              ### Run chain to structure pdf search results
              try:
                pdf_object = chain.run(output)
              except Exception as e:
                print(f"something bad happened: {e}")
              else:
                ### Get first object returned from extraction chain
                if isinstance(pdf_object, list):
                  pdf_object = next(iter(pdf_object))
                print(pdf_object)

                ### Set variables to determine if pdf is useful
                related = pdf_object["related"]
                document_type = pdf_object["document_type"]

                ### If PDF is detmermined to be useful, add it to the resource urls list
                if related == True and document_type != None:
                    resource = {"type": document_type, "url": new_link}
                    resource_urls.append(resource)
                    if pdf_object.get("other_models"):
                      if isinstance(pdf_object["other_models"], list):
                        print(f"other models: {pdf_object['other_models']}")
                        for other_model in pdf_object["other_models"].split(","):
                          related_models.append(other_model)
                      else:
                        related_models.append(pdf_object["other_models"])
                else:
                  bad_urls.append(new_link)

  print("end pdf search")                
  return model_number