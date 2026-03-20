from dotenv import load_dotenv  # wird nur lokal für debug_local.py gebraucht
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import asyncio
import json
import random

async def setup_browser(cookies_json: str, account_name: str = ""):
    """Startet einen Browser-Kontext für einen Account.
    
    cookies_json: JSON-String der Cookies (aus ENV-Variable)
    account_name: Name des Accounts für Logging
    """
    if not cookies_json:
        raise ValueError(
            f"Cookies für Account '{account_name}' nicht gesetzt! "
            "Führe export_cookies.py lokal aus und trage den Output in Railway ein."
        )

    cookies = json.loads(cookies_json)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900},
        locale="de-DE",
        timezone_id="Europe/Berlin",
        color_scheme="light",
        extra_http_headers={
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
    )

    await context.add_cookies(cookies)

    # Stealth auf Context-Ebene anwenden → gilt automatisch für alle neuen Seiten
    Stealth().hook_playwright_context(context)

    # Session-Check
    page = await context.new_page()
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
    if "authwall" in page.url or "login" in page.url or "checkpoint" in page.url:
        await browser.close()
        await playwright.stop()
        raise Exception(
            f"Cookies ungültig oder abgelaufen (Weitergeleitet zu: {page.url}). "
            "Führe export_cookies.py erneut aus und aktualisiere LINKEDIN_COOKIES in Railway."
        )
    await page.close()  # Session-Check Seite schließen

    print(f"✅ Browser bereit für Account '{account_name}' (Cookies geladen)")
    return browser, context, playwright

async def close_browser(browser, playwright):
    await browser.close()
    await playwright.stop()

def format_german_date(date_str):
    months_de = {
        "Januar": "01", "Februar": "02", "März": "03", "April": "04",
        "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
        "September": "09", "Oktober": "10", "November": "11", "Dezember": "12",
        # Deutsche Abkürzungen
        "Jan": "01", "Feb": "02", "Mär": "03", "Apr": "04",
        "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", 
        "Okt": "10", "Nov": "11", "Dez": "12"
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

async def _random_delay(min_s=1.5, max_s=4.0):
    """Zufällige menschliche Verzögerung."""
    await asyncio.sleep(random.uniform(min_s, max_s))

async def get_vernetzt_seit(profile_url, context):
    # Stelle sicher, dass die URL mit / endet
    if not profile_url.endswith('/'):
        profile_url = profile_url + '/'
    contact_url = profile_url + 'overlay/contact-info/'

    # Neue Seite pro Request - verhindert dass ein Crash alle weiteren Requests blockiert
    page = await context.new_page()

    try:
        # Erst das Profil laden (menschliches Verhalten)
        await page.goto(profile_url, wait_until="domcontentloaded", timeout=20000)

        # Checkpoint / Bot-Erkennung abfangen
        if any(x in page.url for x in ["checkpoint", "authwall", "login"]):
            print(f"[WARNUNG] LinkedIn Bot-Check erkannt: {page.url}")
            await page.close()
            return "BLOCKED"

        await _random_delay(2.0, 5.0)

        # Kurz scrollen wie ein Mensch
        await page.mouse.wheel(0, random.randint(200, 600))
        await _random_delay(1.0, 2.5)

        # Dann zur Contact-Info navigieren
        await page.goto(contact_url, wait_until="domcontentloaded", timeout=15000)
        await _random_delay(1.0, 2.0)
    except Exception as e:
        print(f"[DEBUG] Goto-Fehler: {e}")
        await page.close()
        return "Nicht vernetzt oder Fehler"
    
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
        await page.close()
        return "Nicht vernetzt"
    
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
    
    await page.close()

    if formatted_date:
        return formatted_date
    else:
        return "Vernetzt (Datum nicht gefunden)"


