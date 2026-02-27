from dotenv import load_dotenv
import os
from playwright.async_api import async_playwright
import asyncio

async def setup_browser():
        load_dotenv()
        EMAIL = os.getenv("LINKEDIN_EMAIL")
        PASSWORD = os.getenv("LINKEDIN_PASS")
        
        if not EMAIL or not PASSWORD:
            print("[DEBUG] ⚠️ FEHLER: LINKEDIN_EMAIL oder LINKEDIN_PASS nicht gesetzt!")
            raise Exception("Missing LinkedIn credentials")
        
        print(f"[DEBUG] Login mit Email: {EMAIL[:5]}***")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("[DEBUG] Gehe zu LinkedIn Login...")
            await page.goto("https://www.linkedin.com/login")
            
            print("[DEBUG] Fülle Email aus...")
            await page.fill("input#username", EMAIL)
            await page.fill("input#password", PASSWORD)
            
            print("[DEBUG] Klicke Submit...")
            await page.click("button[type='submit']")
            
            # Warte bis eingeloggt
            print("[DEBUG] Warte auf Login...")
            await page.wait_for_url("https://www.linkedin.com/feed/**", timeout=15000)
            
            print("[DEBUG] ✓ LOGIN ERFOLGREICH!")
            
        except Exception as e:
            print(f"[DEBUG] ✗ LOGIN FEHLER: {e}")
            print(f"[DEBUG] Aktuelle URL: {page.url}")
            raise
        
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
    
    # Debug: Gesamtes HTML ausgeben
    html = await page.content()
    print(f"[DEBUG] Seite hat {len(html)} Zeichen")
    
    # Suche nach dem p-Element mit "Vernetzt seit" oder "Connected since"
    vernetzt_header = page.locator("p:has-text('Vernetzt seit'), p:has-text('Connected since')")
    
    try:
        await vernetzt_header.wait_for(timeout=5000)
        print("[DEBUG] ✓ 'Vernetzt seit' Header gefunden")
        
        # Hole das HTML des gefundenen Elements
        header_html = await vernetzt_header.evaluate("el => el.outerHTML")
        print(f"[DEBUG] Header HTML: {header_html[:200]}")
        
    except Exception as e:
        print(f"[DEBUG] ✗ 'Vernetzt seit' Header NICHT gefunden")
        print(f"[DEBUG] Fehler: {e}")
        
        # Debug: Alle p-Elemente ausgeben
        all_p = await page.locator('p').all()
        print(f"[DEBUG] Alle P-Elemente ({len(all_p)}):")
        for i, p in enumerate(all_p[:10]):  # Erste 10
            text = await p.inner_text()
            print(f"  [{i}] {text[:100]}")
        
        # Debug: HTML-Content prüfen
        if "Vernetzt seit" not in html and "Connected since" not in html:
            print("[DEBUG] ⚠️ 'Vernetzt seit' oder 'Connected since' NICHT im HTML!")
            print("[DEBUG] URL war:", page.url)
        
        return "Nicht vernetzt"
    
    # Das Datum ist im nächsten p-Element Sibling
    date_element = vernetzt_header.locator("xpath=following-sibling::p[1]")
    
    try:
        await date_element.wait_for(timeout=3000)
        raw_date = await date_element.inner_text()
        print(f"[DEBUG] ✓ Datum gefunden: '{raw_date}'")
        formatted_date = format_german_date(raw_date.strip())
        print(f"[DEBUG] ✓ Formatiert: '{formatted_date}'")
        return formatted_date
    except Exception as e:
        print(f"[DEBUG] ✗ Datum NICHT gefunden")
        print(f"[DEBUG] Fehler: {e}")
        return "Vernetzt (Datum nicht gefunden)"


