import asyncio, os
import json
import logging
import time
from ratelimit import limits, sleep_and_retry
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.prompts import PromptTemplate
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import deque, defaultdict
from utlis.config import GEMINI_API_KEY, MEMORY_FILEPATH, SIMILARITY_THRESHOLD, MAX_MEMORY_PER_EXPERT
from src.services.gemini2 import LLM
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Setup logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s, %(levelname)s: %(message)s")

class LLMMemory:
    def __init__(self, model_name:str, generation_config:dict, safety_settings:dict):
        """
            Initialize model, memory, and vectorstore
        """
        # Load Gemini Pro model
        try:
            self.model = LLM # Use passed LLM instant for modularity
        except Exception as e:
            logging.error(f"Failed to load Gemini Pro model: {e}")
            return RuntimeError(f"Failed to load Gemini Pro model: {e}")
        
        # Initialize memory storage as context windows for each user/channel (temporary in-session memory)
        self.context_windows = defaultdict(lambda: defaultdict(list)) 

        # Load persistent conversation memory
        self.memory = self.load_memory()

        # Initialize model embeddings and vector store for context retrieval
        self.embeddings = GoogleGenerativeAIEmbeddings(model="model/text-embedding-001")
        self.vectorstore = DocArrayInMemorySearch.from_texts(
            [  # set mini docs for embedding (used to train the vector store prioritize conversation context when retrieving relevant past messages)
                "This system tracks ongoing conversations between users and experts, ensuring continuity and context-aware responses.",
                "Each user has a dedicated context window storing their last 10 interactions, allowing for smooth follow-up discussions."
                "Context windows are tied to a user id (private chat) or channel id (group chat) to maintain proper conversation history.", "Routing decisions consider the entire conversation history, preventing users from being incorrectly reassigned to different experts.", "The system summarizes older messages to retain key details while optimizing memory usage."
            ],
            embeddings=self.embeddings
        )

        # Initialize retriever
        self.retriever = self.vectorstore.as_retriever()

        # Define prompt format for context-aware responses
        template = """Answer the question based on the following context:
        {context}
        Conversation History:
        {history}
        Question: {question}
        """
        self.prompt = PromptTemplate.from_template(template)

    def load_memory(self):
        """
            Load conversation memory from JSON file.
        """
        if os.path.exists(MEMORY_FILEPATH):
            with open(MEMORY_FILEPATH, "r") as file:
                return json.load(file)
        return {}
    
    def save_memory(self):
        """
            Save conversation memory to JSON file.
        """
        with open(MEMORY_FILEPATH, 'w') as file:
            json.dump(self.memory, file, indent=4)

    def detect_context_shift(self, user_id:str, expert_name:str, new_query:str) -> bool:
        """
        Determine if a topic shift has occurred by comparing the new query to existing context. Return True if the topic has shifted, otherwise False.
        """
        if not self.context_windows[user_id][expert_name]:
            return False # no previous messages, no shift
        context_texts = [" ".join(q for q,r in self.context_windows[user_id][expert_name])]
        context_embeddings = self.embeddings.embed(context_texts)
        query_embeddings = self.embeddings.embed(new_query) 
        similarities = cosine_similarity([query_embeddings], context_embeddings)[0]
        max_similarity = np.max(similarities)

        return max_similarity < SIMILARITY_THRESHOLD # shift detected if similarity is low

    def update_context_window(self, user_id:str, expert_name:str, question:str, response:str) -> None:
        """
            Update the context window dynamically. If a context shift is detected, label and store old context and start a new window.
        """
        # Detect context shift
        if self.detect_context_shift(user_id, expert_name, question):
            self.context_windows[user_id][expert_name] = {"messages": [], "topic": question}

        # Add new message
        self.context_windows[user_id][expert_name]["messages"].append((question, response))

        # Store entire context in vector embeddings for better retrieval
        history = "\n".join([f"User: {q}\nBot: {a}" for q,a in self.context_windows[user_id][expert_name]["messages"]])
        self.vectorstore.add_texts([history])

    def store_conversation(self, user_id:str, expert_name:str):
        """
            Store past conversations in memory, ensuring each user has only 5 stored context windows per expert.
        """
        messages = self.context_windows[user_id][expert_name]
        if not messages:
            return # No data to store if no messages
        
        # Ensure the user and expert exist in memory
        if user_id not in self.memory:
            self.memory[user_id] = {}
        if expert_name not in self.memory[user_id]:
            self.memory[user_id][expert_name] = []

        new_entry = {
            "context": messages["topic"],
            "messages": messages["messages"]
        }
        
        self.memory[user_id][expert_name].append(new_entry)
        
        # Maintain memory limit per expert
        if len(self.memory[user_id][expert_name]) > MAX_MEMORY_PER_EXPERT:
            self.memory[user_id][expert_name].pop(0)

        self.save_memory()

    def get_context_window(self, user_id:str, expert_name:str) -> str:
        """
            Retrieve last CONTEXT_WINDOW_SIZE interactions from user's conversation history.
        """
        messages = self.context_windows[user_id][expert_name]["messages"]
        return "\n".join([f"Question: {q}\nResponse: {r}" for q, r in messages]) if messages else "No prior history :("

    async def query(self, user_id:str, expert_name:str, question:str):
        """
            Query the LLM while considering user context.
        """
        try: 
            # Retrieve relevant context from the vectorstore
            context_docs = self.retriever.get_relevant_documents(question)
            context = " ".join([doc.page_content for doc in context_docs])

            # Get conversation history
            history = self.get_context_window(user_id, expert_name)

            # Format input prompt
            chain_input = {
                "context": context,
                "history": history,
                "question": question
            }
            formatted_prompt = self.prompt.format(**chain_input)

            # Generate response asynchronously
            response = await self.llm.query(formatted_prompt)

            # Update context window
            self.update_context_window(user_id, expert_name, question, response)
        except Exception as e:
            logging.error(f"Failed to query model: {e}")
            return f"Error: {e}"


async def run_model_with_memory(user_id:str, expert_name:str, prompt:str, llm:LLM) -> str:
    """
        Run Gemini Pro with context window tracking.
    """
    memory = LLMMemory(llm)
    response = await memory.query(user_id, expert_name, prompt)
    return response
