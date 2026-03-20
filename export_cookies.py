"""
Führe dieses Script LOKAL aus um LinkedIn-Cookies zu exportieren.
Danach den ausgegebenen JSON-String als ENV-Variable in Railway eintragen.

Ausführen:
  python export_cookies.py bjorn
  python export_cookies.py dennis
  python export_cookies.py ute
"""
import asyncio
import json
import sys
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

ACCOUNT_CONFIG = {
    "bjorn":  {"email_env": "LINKEDIN_EMAIL_BJORN",  "pass_env": "LINKEDIN_PASS_BJORN",  "env_key": "LINKEDIN_COOKIES_BJORN"},
    "dennis": {"email_env": "LINKEDIN_EMAIL_DENNIS", "pass_env": "LINKEDIN_PASS_DENNIS", "env_key": "LINKEDIN_COOKIES_DENNIS"},
    "ute":    {"email_env": "LINKEDIN_EMAIL_UTE",    "pass_env": "LINKEDIN_PASS_UTE",    "env_key": "LINKEDIN_COOKIES_UTE"},
}

async def main():
    load_dotenv()

    if len(sys.argv) < 2 or sys.argv[1].lower() not in ACCOUNT_CONFIG:
        print("❌ Bitte Account angeben: python export_cookies.py [bjorn|dennis|ute]")
        sys.exit(1)

    account = sys.argv[1].lower()
    config = ACCOUNT_CONFIG[account]

    EMAIL = os.getenv(config["email_env"])
    PASSWORD = os.getenv(config["pass_env"])

    if not EMAIL or not PASSWORD:
        print(f"❌ {config['email_env']} und {config['pass_env']} nicht in .env gesetzt!")
        sys.exit(1)

    print(f"🔐 Öffne Browser für LinkedIn Login ({account})...")

    async with async_playwright() as p:
        # Sichtbarer Browser damit du ggf. CAPTCHA/2FA lösen kannst
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )
        page = await context.new_page()

        await page.goto("https://www.linkedin.com/login")
        await page.fill("input#username", EMAIL)
        await page.fill("input#password", PASSWORD)
        await page.click("button[type='submit']")

        print("⏳ Warte auf Login... (löse ggf. CAPTCHA/2FA im Browser)")
        try:
            await page.wait_for_url("**/feed/**", timeout=60000)
        except:
            print("⚠️  Kein Feed erkannt – prüfe ob du eingeloggt bist und drücke Enter")
            input("  → Wenn du eingeloggt bist, drücke Enter um fortzufahren...")

        cookies = await context.cookies()
        await browser.close()

    cookies_json = json.dumps(cookies)
    output_file = f"linkedin_cookies_{account}.json"

    with open(output_file, "w") as f:
        f.write(cookies_json)

    print(f"\n✅ Cookies für '{account}' exportiert!")
    print("=" * 60)
    print(f"Kopiere diesen Wert als {config['env_key']} in Railway:\n")
    print(cookies_json)
    print("=" * 60)
    print(f"\nBackup gespeichert in '{output_file}'.")

asyncio.run(main())
