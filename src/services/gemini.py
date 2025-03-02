import google.generativeai as genai
import asyncio, os
import logging
import time
from ratelimit import limits, sleep_and_retry

from utlis.config import GEMINI_API_KEY, RATE_LIMIT


# Setup logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s, %(levelname)s: %(message)s")

class LLM():
    def __init__(self, model_name:str, generation_config:dict, safety_settings:dict):
        # Load model
        try:
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            logging.error(f"Failed to load {model_name} model: {e}")
            raise RuntimeError(f"Failed to load {model_name} model: {e}")

    # Query Model: Set rate limit to RATE_LIMIT RPM / user
    @sleep_and_retry
    @limits(calls=RATE_LIMIT, period=60)
    async def query(self, prompt:str) -> str: # let model response be ansynchronous to allow for concurrency
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt) # can't access generate_content() method asynchronously --> access, then make asynchronous
            return response.text.strip()
        except Exception as e:
            logging.error(f"Failed to query {self.model.model_name} model: {e}")
            return f"Failed to query {self.model.model_name} model: {e}"

# Function to run model
async def run_model(prompt, model_name:str, generation_config:dict, safety_settings:dict) -> str:
    response = await LLM(model_name, generation_config, safety_settings).query(prompt)
    return response

