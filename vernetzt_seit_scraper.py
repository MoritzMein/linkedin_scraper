from dotenv import load_dotenv
import os
from playwright.async_api import async_playwright
import asyncio

async def setup_browser():
        load_dotenv()
        EMAIL = os.getenv("LINKEDIN_EMAIL")
        PASSWORD = os.getenv("LINKEDIN_PASS")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        await page.fill("input#username", EMAIL)
        await page.fill("input#password", PASSWORD)
        await page.click("button[type='submit']")
        return browser, page, playwright

async def close_browser(browser, playwright):
    await browser.close()
    await playwright.stop()

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

async def get_vernetzt_seit(profile_url, page):
    # Stelle sicher, dass die URL mit / endet, bevor wir overlay anhängen
    if not profile_url.endswith('/'):
        profile_url = profile_url + '/'
    profile_url = profile_url + 'overlay/contact-info/'
    try:
        # Nutze "domcontentloaded" statt "networkidle" für schnellere Antworten
        await page.goto(profile_url, wait_until="domcontentloaded", timeout=15000)
    except Exception as e:
        print(f"[DEBUG] Goto-Fehler: {e}")
        # Versuche trotzdem zu scrapen, vielleicht ist die Seite teilweise geladen
        pass
    
    # Suche nach dem p-Element mit "Vernetzt seit" oder "Connected since"
    vernetzt_header = page.locator("p:has-text('Vernetzt seit'), p:has-text('Connected since')")
    
    try:
        await vernetzt_header.wait_for(timeout=5000)
    except:
        # Debug: Was ist auf der Seite?
        print(f"[DEBUG] URL: {page.url}")
        print(f"[DEBUG] Alle p-Texte: {await page.locator('p').all_inner_texts()}")
        return "Nicht vernetzt"
    
    # Das Datum ist im nächsten p-Element Sibling
    date_element = vernetzt_header.locator("xpath=following-sibling::p[1]")
    
    try:
        await date_element.wait_for(timeout=3000)
        raw_date = await date_element.inner_text()
        formatted_date = format_german_date(raw_date.strip())
        return formatted_date
    except:
        return "Vernetzt (Datum nicht gefunden)"


