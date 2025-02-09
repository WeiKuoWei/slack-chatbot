import google.generativeai as genai
import asyncio, os
import logging
import time
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from ratelimit import limits, sleep_and_retry
from utils.config import GEMINI_API_KEY

# Setup logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s, %(levelname)s: %(message)s")

'''
Currently passed in as a global variable. 
Might need to create a separate configuration file in the future. 
'''
GENERATION_CONFIG = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2048,
}

class Gemini:
    def __init__(self):

        genai.configure(api_key=GEMINI_API_KEY)
        
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
        }

        # Defining rate limits
        self.rate_limits = {
            "gemini-1.5-pro": (2, 60),
            "gemini-1.5-flash": (15, 60)
        }

    @sleep_and_retry
    async def query(self, prompt, model_name="gemini-1.5-pro"):
        if model_name not in self.rate_limits:
            raise ValueError(f"Invalid model name. Choose from {list(self.rate_limits.keys())}")

        calls, period = self.rate_limits[model_name]

        '''
        Though genai.GenerativeModel seems to be a lightweight initialization, 
        might consider caching (model={}) for performance. 
        '''
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=GENERATION_CONFIG,
            safety_settings=self.safety_settings
        )

        # Nested function to customize calls and periods
        @limits(calls=calls, period=period)
        async def _query():
            try:
                response = await asyncio.to_thread(model.generate_content, prompt)
                return response.text.strip()
            except Exception as e:
                logging.error(f"Failed to query {model_name} model: {e}")
                return f"Failed to query {model_name} model: {e}"
        
        return await _query()

# "gemini-1.5-pro" by default
async def run_gemini(prompt, model_name="gemini-1.5-pro"):
    response = await Gemini().query(prompt, model_name)
    return response
