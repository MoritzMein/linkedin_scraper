"""
Debug-Skript zum lokalen Testen des LinkedIn-Scrapers ohne Server
Verwendung: python debug_local.py
"""

import os
import asyncio
from dotenv import load_dotenv
from vernetzt_seit_scraper import setup_browser, close_browser, get_vernetzt_seit


async def test_scraper():
    """Testet den Scraper mit lokalen Profil-URLs"""
    
    # Test-URLs
    test_profiles = [
        'https://linkedin.com/in/miroslav-marjanovic-7baa42138'
    ]
    
    print("🚀 Starte Browser-Setup...")
    try:
        browser, page, playwright = await setup_browser()
        print("✅ Browser gestartet\n")
        
        # Warte kurz nach Login
        await asyncio.sleep(3)
        
        # Teste jeden Profile
        for profile_url in test_profiles:
            print(f"📍 Teste: {profile_url}")
            try:
                result = await get_vernetzt_seit(profile_url, page)
                print(f"   ✓ Ergebnis: {result}\n")
            except Exception as e:
                print(f"   ✗ Fehler: {e}\n")
        
    except Exception as e:
        print(f"❌ Setup-Fehler: {e}")
    finally:
        print("🛑 Schließe Browser...")
        await close_browser(browser, playwright)
        print("✅ Fertig")


if __name__ == "__main__":
    asyncio.run(test_scraper())
