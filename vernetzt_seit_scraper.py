from dotenv import load_dotenv
import os
from playwright.async_api import async_playwright
import asyncio



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
    profile_url = profile_url + 'overlay/contact-info/'
    await page.goto(profile_url)
    
    # Prüfen, ob der "Vernetzt"-Reiter (Header) sichtbar ist
    vernetzt_header = page.locator("h3.pv-contact-info__header:has-text('Vernetzt')")
    
    if await vernetzt_header.is_visible():
        # Optional: Das Datum auslesen
        date_element = vernetzt_header.locator("xpath=..").locator(".t-black.t-normal")
        if await date_element.is_visible():
            raw_date = await date_element.inner_text()
            formatted_date = format_german_date(raw_date.strip())
            return formatted_date
    
    return "Nicht vernetzt"

