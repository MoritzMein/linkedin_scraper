from fastapi import FastAPI
from pydantic import BaseModel
from vernetzt_seit_scraper import get_vernetzt_seit, setup_browser, close_browser

app = FastAPI()
browser = None
page = None
playwright = None

class ProfileRequest(BaseModel):
    profile_url: str

@app.on_event("startup")
async def startup_event():
    global browser, page, playwright
    browser, page, playwright = await setup_browser()

@app.on_event("shutdown")
async def shutdown_event():
    global browser, playwright
    await close_browser(browser, playwright)

@app.post("/vernetzt_seit/")
async def vernetzt_seit(request: ProfileRequest):
    global page
    result = await get_vernetzt_seit(request.profile_url, page)
    return {"vernetzt_seit": result}
