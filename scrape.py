import os
from playwright.sync_api import sync_playwright


def create(playwright):
  is_dev = os.getenv('ENVIRONMENT') == 'development'
  browser = playwright.chromium.launch(
    headless=(not is_dev), slow_mo=50 if is_dev else 0)
  context = browser.new_context()
  page = context.new_page()
  return page, context, browser


def scrape_with_context(scraper):
  with sync_playwright() as playwright:
    page, context, browser = create(playwright)
    result = scraper(page, context=context)
    browser.close()
    return result


def scrape(scraper):
  with sync_playwright() as playwright:
    page, _, browser = create(playwright)
    result = scraper(page)
    browser.close()
    return result
