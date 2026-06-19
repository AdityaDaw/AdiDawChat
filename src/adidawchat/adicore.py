import os
from profile import get_chrome_profile_dir
import asyncio
import platform
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright

HEADLESS = True

USER_DATA_DIR = get_chrome_profile_dir()



@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                channel="chrome", 
                headless=HEADLESS,
                # ARGS TO EVADE DETECTION (STEALTH MODE)
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled", # Crucial: Hides the automation flag
                    "--no-sandbox",
                    "--disable-infobars",
                ],
                no_viewport=True,
                # Essential: Explicitly tell Chrome NOT to show up as a bot
                ignore_default_args=["--enable-automation"] 
            )
    
    for page in browser.pages:
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    if len(browser.pages) > 0:
        page_a = browser.pages[0]
    else:
        page_a = await browser.new_page()
            
    await page_a.goto("https://gemini.google.com/app/91ffa4302ca82f8f")

    # Store objects in app.state so they are accessible in routes
    app.state.playwright = playwright
    app.state.browser = browser
    app.state.page = page_a
    app.state.lock = asyncio.Lock()  # Prevents overlapping browser actions
    
    yield  # The API runs while this is suspended
    
    # --- Shutdown Logic ---
    await browser.close()
    await playwright.stop()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    prompt: str

@app.post("/v1/chat")
async def chat(request: ChatRequest):
    page = app.state.page
    lock = app.state.lock

    # Acquire the lock so multiple API calls queue up nicely instead of breaking the page state
    async with lock:
        try:
            # 1. Target the input field (Gemini uses contenteditable divs for input)
            input_selector = 'div[contenteditable="true"], textarea'
            await page.wait_for_selector(input_selector, timeout=10000)
            
            # 2. Focus and enter the text
            await page.click(input_selector)
            await page.fill(input_selector, request.prompt)
            
            # 3. Submit via pressing Enter
            await page.press(input_selector, "Enter")
            
            # 4. Wait for Gemini to finish generating text
            # We can use a general layout pause or watch for element updates.
            # Adjust the timeout duration depending on typical response times.
            await page.wait_for_timeout(6000) 
            
            # 5. Extract the latest response block from the chat interface
            # These selectors match standard layout classes for dynamic chat outputs
            response_selector = 'message-content, .model-response, .message-text'
            responses = await page.locator(response_selector).all()
            
            if responses:
                # Fetch text from the absolute newest response container on the DOM
                last_response_text = await responses[-1].inner_text()
                return {"status": "success", "response": last_response_text.strip()}
            else:
                return {
                    "status": "partial_success", 
                    "message": "Prompt submitted, but the response text wrapper could not be parsed."
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Browser automation execution failed: {str(e)}")
        

if __name__ == "__main__":
    print(__file__)