import google.generativeai as genai
import asyncio, os
import logging
import time
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from ratelimit import limits, sleep_and_retry
from utils.config import GEMINI_API_KEY

# Setup logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s, %(levelname)s: %(message)s")

class Gemini:
    def __init__(self):
        # Load API key
        if not GEMINI_API_KEY:
            logging.error("GEMINI_API_KEY is missing from envrionment variables.")
            raise ValueError("GEMINI_API_KEY is undefined.")
        genai.configure(api_key=GEMINI_API_KEY)

        # Load Gemini with specific generation and safety settings
        generation_config = {
            "temperature": 0.4,
            "top_p": 1,
            "top_k":32,
            "max_output_tokens": 2048
        }
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
        }

        # Load Gemini-1.5-Pro model
        try:
            self.Pro = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            logging.error(f"Failed to load Gemini-1.5-Pro model: {e}")
            raise RuntimeError(f"Failed to load Gemini-1.5-Pro model: {e}")
        
        # Load Gemini-1.5-Flash model
        try:
            self.Flash = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            logging.error(f"Failed to load Gemini-1.5-Flash model: {e}")
            raise RuntimeError(f"Failed to load Gemini-1.5-Flash model: {e}")

    # Query Gemini Pro: Set rate limit to 2 RPM / user
    @sleep_and_retry
    @limits(calls=2, period=60)
    async def pro_query(self, prompt): # let model response be ansynchronous to allow for concurrency
        try:
            response = await asyncio.to_thread(self.Pro.generate_content, prompt) # can't access generate_content() method asynchronously --> access, then make asynchronous
            return response.text.strip()
        except Exception as e:
            logging.error(f"Failed to query Gemini-1.5-Pro model: {e}")
            return f"Failed to query Gemini-1.5-Pro model: {e}"
        
    # Query Gemini Flash: Set rate limit to 15 RPM / user
    @sleep_and_retry
    @limits(calls=15, period=60)   # 15 RPM 
    async def flash_query(self, prompt): # let model response be ansynchronous to allow for concurrency
        try:
            response = await asyncio.to_thread(self.Flash.generate_content, prompt) # can't access generate_content() method asynchronously --> access, then make asynchronous
            return response.text.strip()
        except Exception as e:
            logging.error(f"Failed to query Gemini-1.5-Flash model: {e}")
            return f"Failed to query Gemini-1.5-Flash model: {e}"

# Function to run Gemini-1.5-Pro
async def run_gemini_pro(prompt):
    response = await Gemini().pro_query(prompt)
    return response

# Function to run Gemini-1.5-Flash
async def run_gemini_flash(prompt):
    response = await Gemini().flash_query(prompt)
    return response
