from celery_app import celery_app
from scrape import scrape


@celery_app.task
def register_carrier_warranty(payload):
  print(payload)

  def scraper(page):
    error = False
    download = None
    page.goto(
      "https://productregistration.carrier.com/public/RegistrationForm_Carrier?brand=CARRIER")
    page.locator("#Products_0__SerialNumber").fill("2524V61940")
    page.locator("#Products_0__SerialNumber").click()
    page.locator("div").filter(
      has_text="PRODUCT REGISTRATION 1 Serial").nth(1).click()
    page.get_by_role("row", name="2524V61940 KFFEH2601C10").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="2524V61940 KFFEH2601C10").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="2524V61940 KFFEH2601C10").get_by_placeholder(
      "MM/DD/YYYY").fill("09/28/2024")
    page.locator("div").filter(
      has_text="PRODUCT REGISTRATION 1 Serial").nth(1).click()
    page.locator("#Products_1__SerialNumber").click()
    page.locator("#Products_1__SerialNumber").fill("3024C62073")
    page.locator("#Products_1__SerialNumber").click()
    page.get_by_role("row", name="3024C62073 Refresh").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="3024C62073 GA5SAN43600W").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="3024C62073 GA5SAN43600W").get_by_placeholder(
      "MM/DD/YYYY").fill("09/28/2024")
    page.get_by_role("row", name="Refresh", exact=True).get_by_placeholder(
      "Enter serial number").click()
    page.get_by_role("row", name="Refresh", exact=True).get_by_placeholder(
      "Enter serial number").fill("2624F03703")
    page.get_by_role("row", name="Refresh", exact=True).get_by_placeholder(
      "Enter serial number").click()
    page.get_by_role("row", name="2624F03703 FJ4DNXB36L00").get_by_placeholder(
      "MM/DD/YYYY").click()
    page.get_by_role("row", name="2624F03703 FJ4DNXB36L00").get_by_placeholder(
      "MM/DD/YYYY").fill("9/28/2024")
    page.locator("div").filter(
      has_text="PRODUCT REGISTRATION 1 Serial").nth(1).click()
    page.get_by_role("img", name="Delete").click()
    page.get_by_role(
      "row", name="2624F03703 FJ4DNXB36L00 9/28/").get_by_placeholder("MM/DD/YYYY").dblclick()
    page.get_by_role("link", name="28").click()
    page.get_by_label("Replacement of existing").check()
    page.get_by_label("Replacement of existing").check()
    page.get_by_label("Residential Single Family").check()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_role("button", name="Next", exact=True).click()
    page.get_by_placeholder("Enter first name").click()
    page.get_by_placeholder("Enter first name").fill("Tige Brown")
    page.get_by_placeholder("Enter first name").click()
    page.get_by_placeholder("Enter first name").click()
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("Shift+ArrowLeft")
    page.get_by_placeholder("Enter first name").press("ControlOrMeta+x")
    page.get_by_placeholder("Enter first name").fill("Tige")
    page.get_by_placeholder("Enter last name").click()
    page.get_by_placeholder("Enter last name").fill("Brown")
    page.get_by_role("textbox", name="Enter address", exact=True).click()
    page.get_by_role("textbox", name="Enter address", exact=True).fill(
      "4045 North Indigo Drive, Harvey, LA 70058")
    page.get_by_role("textbox", name="Enter address", exact=True).click()
    page.locator("#ui-id-10").click()
    page.get_by_label("Check here if you don't have").check()
    page.get_by_label("Check here if you don't have").uncheck()
    page.locator("#txtConsumerEmail").click()
    page.locator("#txtConsumerEmail").click()
    page.locator("#txtConsumerConfirmEmail").click()
    page.locator("#txtConsumerConfirmEmail").click()
    page.get_by_label("Check here if you don't have").check()
    page.get_by_label("Check here if your address is").check()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_role("textbox", name="(999) 999-").click()
    page.get_by_role(
      "textbox", name="(999) 999-").fill("(2258036441___) ___-____")
    page.locator("#webcontent1").click()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_role("textbox", name="Enter address", exact=True).click()
    page.get_by_role("textbox", name="Enter zip code").click()
    page.get_by_text("Step 3 of 6: Equipment").click()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_text("Step 4 of 6: DEALER").click()
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("textbox", name="Please contact your").fill("Keefes")
    page.get_by_role("button", name=" Search").click()
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("textbox", name="Please contact your").fill("Keefe")
    page.get_by_role("textbox", name="Please contact your").click()
    page.get_by_role("button", name=" Search").click()
    page.get_by_text("MFG Account # 181418-").click()
    page.get_by_text("MFG Account # 181418-").click(click_count=5)
    page.get_by_text("MFG Account # 181418-").dblclick()
    page.get_by_text("MFG Account # 181418-").click()
    page.get_by_label("Keefe's A/C & Heating Inc").check()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_text("Step 5 of 6: Warranty Details").click()
    page.get_by_role("button", name="Next   ").click()
    page.get_by_text("Step 6 of 6: Review & Submit").click()
    page.get_by_role("button", name="Submit   ").click()
    page.get_by_role("button", name="Yes").click()
    page.get_by_role("button", name="PRINT   ").click()
    page.get_by_text("Z006215691190C").click()

  scrape(scraper)
