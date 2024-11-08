
import google.generativeai as genai
import asyncio, os
import logging
import time
from ratelimit import limits, sleep_and_retry

# Setup logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s, %(levelname)s: %(message)s")

class GeminiPro:
    def __init__(self):
        # Load API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.error("GEMINI_API_KEY is missing from envrionment variables.")
            raise ValueError("GEMINI_API_KEY is undefined.")
        genai.configure(api_key=api_key)

        # Load Gemini-1.5-Pro model
        try:
            self.model = genai.GenerativeModel("gemini-1.5-pro")
        except Exception as e:
            logging.error(f"Failed to load Gemini-1.5-Pro model: {e}")
            raise RuntimeError(f"Failed to load Gemini-1.5-Pro model: {e}")

    # Set rate limit to 2 RPM / user
    @sleep_and_retry
    @limits(calls=2, period=60)
    async def query(self, prompt, my_project=""): # let model response be ansynchronous to allow for concurrency
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt) # can't access generate_content() method asynchronously --> access, then make asynchronous
            return response.text.strip()
        except Exception as e:
            logging.error(f"Failed to query Gemini-1.5-Pro model: {e}")
            return f"Failed to query Gemini-1.5-Pro model: {e}"
  
class GeminiFlash:
    def __init__(self):
        # Load API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.error("GEMINI_API_KEY is missing from envrionment variables.")
            raise ValueError("GEMINI_API_KEY is undefined")
        genai.configure(api_key=api_key)

        # Load Gemini-1.5-Pro model
        try:
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logging.error(f"Failed to load Gemini-1.5-Flash model: {e}")
            raise RuntimeError(f"Failed to load Gemini-1.5-Flash model: {e}")

    # Set rate limit to 15 RPM / user
    @sleep_and_retry
    @limits(calls=15, period=60)   # 15 RPM 
    async def query(self, prompt): # let model response be ansynchronous to allow for concurrency
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt) # can't access generate_content() method asynchronously --> access, then make asynchronous
            return response.text.strip()
        except Exception as e:
            logging.error(f"Failed to query Gemini-1.5-Flash model: {e}")
            return f"Failed to query Gemini-1.5-Flash model: {e}"

# Function to run Gemini-1.5-Pro
async def run_gemini_pro(prompt):
    response = await GeminiPro().query(prompt)
    return response

# Function to run Gemini-1.5-Flash
async def run_gemini_flash(prompt):
    response = await GeminiFlash().query(prompt)
    return response
