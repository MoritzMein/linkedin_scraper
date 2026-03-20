from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vernetzt_seit_scraper import get_vernetzt_seit, setup_browser, close_browser
import os
from datetime import date
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# {account_name: {"browser": ..., "context": ..., "playwright": ...}}
accounts = {}

# Rate Limiting: {account_name: {"date": date, "count": int}}
rate_limits = defaultdict(lambda: {"date": None, "count": 0})

DAILY_LIMIT = 100

ACCOUNT_ENV_MAP = {
    "bjorn":   "LINKEDIN_COOKIES_BJORN",
    "dennis":  "LINKEDIN_COOKIES_DENNIS",
    "ute":     "LINKEDIN_COOKIES_UTE",
}

class ProfileRequest(BaseModel):
    profile_url: str
    account: str  # "bjorn", "dennis" oder "ute"

@app.on_event("startup")
async def startup_event():
    global accounts
    for name, env_key in ACCOUNT_ENV_MAP.items():
        cookies_json = os.getenv(env_key)
        if cookies_json:
            try:
                browser, context, playwright = await setup_browser(cookies_json, name)
                accounts[name] = {"browser": browser, "context": context, "playwright": playwright}
            except Exception as e:
                print(f"❌ Account '{name}' konnte nicht gestartet werden: {e}")
        else:
            print(f"⚠️  Account '{name}' übersprungen ({env_key} nicht gesetzt)")

@app.on_event("shutdown")
async def shutdown_event():
    for name, acc in accounts.items():
        await close_browser(acc["browser"], acc["playwright"])

@app.post("/vernetzt_seit/")
async def vernetzt_seit(request: ProfileRequest):
    account_name = request.account.lower()

    if account_name not in accounts:
        raise HTTPException(
            status_code=400,
            detail=f"Account '{account_name}' nicht verfügbar. Verfügbar: {list(accounts.keys())}"
        )

    # Rate Limiting prüfen
    today = date.today()
    rl = rate_limits[account_name]
    if rl["date"] != today:
        rl["date"] = today
        rl["count"] = 0

    if rl["count"] >= DAILY_LIMIT:
        return {
            "vernetzt_seit": "RATE_LIMITED",
            "account": account_name,
            "requests_heute": rl["count"],
            "limit": DAILY_LIMIT,
        }

    rl["count"] += 1

    context = accounts[account_name]["context"]
    result = await get_vernetzt_seit(request.profile_url, context)

    return {
        "vernetzt_seit": result,
        "account": account_name,
        "requests_heute": rl["count"],
        "limit": DAILY_LIMIT,
    }

@app.get("/status/")
async def status():
    """Zeigt welche Accounts aktiv sind und wie viele Requests heute gemacht wurden."""
    today = date.today()
    result = {}
    for name in ACCOUNT_ENV_MAP:
        rl = rate_limits[name]
        count = rl["count"] if rl["date"] == today else 0
        result[name] = {
            "aktiv": name in accounts,
            "requests_heute": count,
            "limit": DAILY_LIMIT,
            "verbleibend": max(0, DAILY_LIMIT - count),
        }
    return result
