from dotenv import load_dotenv
import os
from playwright.async_api import async_playwright
import asyncio
import json

async def setup_browser():
    load_dotenv()
    cookies_json = os.getenv("LINKEDIN_COOKIES")

    if not cookies_json:
        raise ValueError(
            "LINKEDIN_COOKIES nicht gesetzt! "
            "Führe export_cookies.py lokal aus und trage den Output in Railway ein."
        )

    cookies = json.loads(cookies_json)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="de-DE",
    )
    page = await context.new_page()
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    await context.add_cookies(cookies)

    # Session-Check
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
    if "authwall" in page.url or "login" in page.url or "checkpoint" in page.url:
        await browser.close()
        await playwright.stop()
        raise Exception(
            f"Cookies ungültig oder abgelaufen (Weitergeleitet zu: {page.url}). "
            "Führe export_cookies.py erneut aus und aktualisiere LINKEDIN_COOKIES in Railway."
        )

    print("✅ Browser bereit (Cookies geladen)")
    return browser, page, playwright

async def close_browser(browser, playwright):
    await browser.close()
    await playwright.stop()

def format_german_date(date_str):
    months_de = {
        "Januar": "01", "Februar": "02", "März": "03", "April": "04",
        "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
        "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
    }
    months_en = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12",
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    
    # Format 1: "27. März 2023" (German)
    # Format 2: "Jul 27, 2023" (English)
    
    parts = date_str.replace(",", "").split()
    
    if len(parts) >= 3:
        # Deutschen Format: ["27.", "März", "2023"]
        if parts[0][-1] == "." and parts[0][0].isdigit():
            day = parts[0].rstrip(".").zfill(2)
            month_name = parts[1]
            year = parts[2]
            
            month = months_de.get(month_name) or months_en.get(month_name)
            if month:
                return f"{day}.{month}.{year}"
        
        # Englisches Format: ["Jul", "27", "2023"]
        elif parts[0] in months_en and parts[1].isdigit():
            month_name = parts[0]
            day = parts[1].zfill(2)
            year = parts[2]
            
            month = months_en.get(month_name)
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
    
    # Suche nach "Vernetzt seit" oder "Connected since" in verschiedenen Element-Typen
    vernetzt_selectors = [
        "p:has-text('Vernetzt seit'), p:has-text('Connected since')",
        "span:has-text('Vernetzt seit'), span:has-text('Connected since')", 
        "div:has-text('Vernetzt seit'), div:has-text('Connected since')",
        "h3:has-text('Vernetzt seit'), h3:has-text('Connected since')",
        "*:has-text('Vernetzt seit'), *:has-text('Connected since')"
    ]
    
    vernetzt_header = None
    for selector in vernetzt_selectors:
        try:
            element = page.locator(selector).first
            await element.wait_for(timeout=2000)
            vernetzt_header = element
            print(f"[DEBUG] Gefunden mit Selector: {selector}")
            break
        except:
            continue
    
    if not vernetzt_header:
        print(f"[DEBUG] URL: {page.url}")
        print(f"[DEBUG] Vernetzt-Header nicht gefunden mit allen Selektoren")
        return "Nicht vernetzt oder Fehler"
    
    # Versuche verschiedene Wege das Datum zu finden
    date_strategies = [
        # Nächstes Sibling Element
        "xpath=following-sibling::*[1]",
        "xpath=following-sibling::p[1]", 
        "xpath=following-sibling::span[1]",
        "xpath=following-sibling::div[1]",
        # Parent und dann nächstes Element
        "xpath=../following-sibling::*[1]",
        "xpath=../../*[contains(text(), '202') or contains(text(), '201')]",
        # Innerhalb des gleichen Containers
        "xpath=../*[contains(text(), '202') or contains(text(), '201')]"
    ]
    
    formatted_date = None
    for strategy in date_strategies:
        try:
            date_element = vernetzt_header.locator(strategy).first
            await date_element.wait_for(timeout=1000)
            raw_date = await date_element.inner_text()
            
            # Prüfe ob das wirklich ein Datum ist
            if any(month in raw_date.lower() for month in ['jan', 'feb', 'mär', 'mar', 'apr', 'mai', 'may', 'jun', 'jul', 'aug', 'sep', 'okt', 'oct', 'nov', 'dez', 'dec']) or any(year in raw_date for year in ['202', '201']):
                formatted_date = format_german_date(raw_date.strip())
                print(f"[DEBUG] Datum gefunden mit: {strategy} -> {raw_date} -> {formatted_date}")
                break
        except:
            continue
    
    if formatted_date:
        return formatted_date
    else:
        return "Vernetzt (Datum nicht gefunden)"


