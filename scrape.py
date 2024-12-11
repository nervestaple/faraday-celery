import os
from playwright.sync_api import sync_playwright

from config import IS_DEV


def create(playwright):
  browser = playwright.chromium.launch(
    headless=(not IS_DEV), slow_mo=50 if IS_DEV else 0)
  context = browser.new_context()
  page = context.new_page()
  return page, context, browser


def scrape(scraper):
  with sync_playwright() as playwright:
    page, _, browser = create(playwright)
    result = scraper(page)
    browser.close()
    return result
