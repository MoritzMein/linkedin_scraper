import os
from time import sleep
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright # <-- NEU

# Lokale, synchrone Setup-Funktion
def setup_browser():
    load_dotenv()
    EMAIL = os.getenv("LINKEDIN_EMAIL")
    PASSWORD = os.getenv("LINKEDIN_PASS")
    # ÄNDERUNG: sync_playwright() verwenden und Variable umbenennen, um Namenskonflikt zu vermeiden
    playwright_instance = sync_playwright().start()
    browser = playwright_instance.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.linkedin.com/login")
    page.fill("input#username", EMAIL)
    page.fill("input#password", PASSWORD)
    page.click("button[type='submit']")
    return browser, page, playwright_instance

def format_german_date(date_str):
    months = {
        "Januar": "01", "Februar": "02", "März": "03", "April": "04",
        "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
        "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
    }
    parts = date_str.split()
    if len(parts) == 3:
        day = parts[0].rstrip(".").zfill(2)
        month_name = parts[1]
        year = parts[2]
        month = months.get(month_name)
        if month:
            return f"{day}.{month}.{year}"
    return date_str

browser, page, playwright = setup_browser()
links = ['https://www.linkedin.com/in/ute-schr%C3%B6der/', 'https://www.linkedin.com/in/katrin-wollert/']

for link in links:
    profile_url = link+'overlay/contact-info/'
    page.goto(profile_url)
    
    # Prüfen, ob der "Vernetzt"-Reiter (Header) sichtbar ist
    vernetzt_header = page.locator("h3.pv-contact-info__header:has-text('Vernetzt')")
    
    if vernetzt_header.is_visible():
        print(f"Vernetzt-Info gefunden für: {link}")
        # Optional: Das Datum auslesen
        date_element = vernetzt_header.locator("xpath=..").locator(".t-black.t-normal")
        if date_element.is_visible():
            raw_date = date_element.inner_text().strip()
            formatted_date = format_german_date(raw_date)
            print(f"Vernetzt seit: {formatted_date}")
    else:
        print(f"Keine Vernetzt-Info gefunden für: {link}")
        
    sleep(2)