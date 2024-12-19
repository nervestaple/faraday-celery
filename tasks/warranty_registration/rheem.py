from typing import Union
from s3 import upload_warranty_pdf_to_s3
from scrape import scrape
from playwright.sync_api import Page


def register_rheem_warranty(payload, systems) -> tuple[Union[str, None], Union[str, None]]:
  log_context = {'job_id': payload['job_id'], 'manufacturer_name': 'rheem'}

  def scraper(page: Page) -> tuple[Union[str, None], Union[str, None]]:
    return None, None

  return scrape(scraper)
