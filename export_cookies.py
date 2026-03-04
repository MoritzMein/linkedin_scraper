"""
Führe dieses Script LOKAL aus um LinkedIn-Cookies zu exportieren.
Danach den ausgegebenen JSON-String als LINKEDIN_COOKIES in Railway eintragen.

Ausführen: python export_cookies.py
"""
import asyncio
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

async def main():
    load_dotenv()
    EMAIL = os.getenv("LINKEDIN_EMAIL")
    PASSWORD = os.getenv("LINKEDIN_PASS")

    if not EMAIL or not PASSWORD:
        raise ValueError("LINKEDIN_EMAIL und LINKEDIN_PASS nicht in .env gesetzt!")

    print("🔐 Öffne Browser für LinkedIn Login...")

    async with async_playwright() as p:
        # Sichtbarer Browser damit du ggf. CAPTCHA/2FA lösen kannst
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        await page.goto("https://www.linkedin.com/login")
        await page.fill("input#username", EMAIL)
        await page.fill("input#password", PASSWORD)
        await page.click("button[type='submit']")

        print("⏳ Warte auf Login... (löse ggf. CAPTCHA/2FA im Browser)")
        # Warte bis du auf dem Feed bist (bis zu 60 Sekunden für manuelle Eingaben)
        try:
            await page.wait_for_url("**/feed/**", timeout=60000)
        except:
            print("⚠️  Kein Feed erkannt – prüfe ob du eingeloggt bist und drücke Enter")
            input("  → Wenn du eingeloggt bist, drücke Enter um fortzufahren...")

        cookies = await context.cookies()
        await browser.close()

    cookies_json = json.dumps(cookies)

    # In Datei speichern (als Backup)
    with open("linkedin_cookies_export.json", "w") as f:
        f.write(cookies_json)

    print("\n✅ Cookies exportiert!")
    print("=" * 60)
    print("Kopiere diesen Wert als LINKEDIN_COOKIES in Railway:\n")
    print(cookies_json)
    print("=" * 60)
    print("\nDie Cookies wurden auch in 'linkedin_cookies_export.json' gespeichert.")

asyncio.run(main())
