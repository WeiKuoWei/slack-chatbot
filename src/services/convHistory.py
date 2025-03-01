import asyncio, os
import logging
import time
from ratelimit import limits, sleep_and_retry
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.prompts import PromptTemplate
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from collections import deque, defaultdict
from utlis.config import GEMINI_API_KEY, RATE_LIMIT

# Setup logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s, %(levelname)s: %(message)s")

# Global configuration
CONTEXT_WINDOW_SIZE = 10 # max number of stored interactions per user
MEMORY_LIMIT = 30 # max number of stored conversations before summarization

class LLMMemory:
    def __init__(self, model_name:str, generation_config:dict, safety_settings:dict):
        # Load Gemini Pro model
        try:
            self.model = ChatGoogleGenerativeAI(
                model=model_name,
                api_key=GEMINI_API_KEY,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            logging.error(f"Failed to load Gemini Pro model: {e}")
            return RuntimeError(f"Failed to load Gemini Pro model: {e}")
        
        # Initialize memory storage as context windows for each user/channel
        self.context_windows = defaultdict(lambda: deque(maxlen=CONTEXT_WINDOW_SIZE)) # keep most recent CONTEXT_WINDOW_SIZE convos (defaultdict will automatically create a key with a default value if key does not exist)
        self.user_conversations = defaultdict(list) # store conversation summaries for each user

        # Initialize model embeddings and vector store for context retrieval
        embeddings = GoogleGenerativeAIEmbeddings(model="model/text-embedding-001")
        self.vectorstore = DocArrayInMemorySearch.from_texts(
            [  # set mini docs for embedding (used to train the vector store prioritize conversation context when retrieving relevant past messages)
                "This system tracks ongoing conversations between users and experts, ensuring continuity and context-aware responses.",
                "Each user has a dedicated context window storing their last 10 interactions, allowing for smooth follow-up discussions."
                "Context windows are tied to a user id (private chat) or channel id (group chat) to maintain proper conversation history.", "Routing decisions consider the entire conversation history, preventing users from being incorrectly reassigned to different experts.", "The system summarizes older messages to retain key details while optimizing memory usage."
            ],
            embedding=embeddings
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

    def update_context_window(self, user_id:str, question:str, response:str) -> None:
        """
            Maintain last CONTEXT_WINDOW_SIZE messages and enforce memory limits. If limit is reached, summarize conversation and clear context window for new interaction entry.
        """
        # If total stored conversations exceeds MEMORY_LIMIT, summarize old data
        if len(self.context_windows[user_id]) == CONTEXT_WINDOW_SIZE:
            self.summarize_conversation(user_id)
            self.context_windows[user_id].clear() # clear context window after summarization

        # Add new convo into context window
        self.context_windows[user_id].append((question,response))


    def get_context_window(self, user_id:str) -> str:
        """
            Retrieve last CONTEXT_WINDOW_SIZE interactions from user's conversation history.
        """
        return "\n".join([f"Question: {q}\nA: {a}" for q, a in self.context_windows[user_id]])
    
    def summarize_conversation(self, user_id:str) -> None:
        """
            Summarize past conversations when CONTEXT_WINDOW_SIZE exceeded to prevent overflow and optimize memory usage. Store summary in user_conversations. Remove old summaries when MEMORY_LIMIT exceeded.
        """
        history = "\n".join([f"User: {q}\nBot: {a}" for q, a in self.context_windows[user_id]])
        summary_prompt = f"Summarize the following conversation:\n{history}"
        try:
            summary = self.model.generate_summary(summary_prompt).text.strip()
        except Exception as e:
            logging.error(f"Failed to generate summary: {e}")
            raise RuntimeError(f"Failed to generate summary: {e}")
        
        # Ensure memory limit is not exceeded
        if len(self.user_conversations[user_id]) == MEMORY_LIMIT:
            self.user_conversations[user_id].popleft() # remove oldest summary
        
        self.user_conversations[user_id].append(summary)

    @sleep_and_retry
    @limits(calls=2, period=60) # Rate limit set to 2RPM per user
    async def query(self, user_id:str, question:str) -> str: # let model response be asynchronous to allow for concurrency
        """
            Query Gemini Pro while considering user context. Use vector retrival and stored conversation history for better responses.
        """
        try:
            # Retrieve relevant docs from vector store
            context_docs = self.retriever.get_relevant_documents(question)
            context = " ".join([doc.page_content for doc in context_docs])

            # Retrieve user-specific most recent conversation history
            history = self.get_context_window(user_id)

            # Format input prompt
            chain_input = {"context": context, "history": history, "question": question}
            formatted_prompt = self.prompt.format(**chain_input)

            # Generate response asynchronously using configured data
            response = await asyncio.to_thread(self.model.generate_content, formatted_prompt)
            response = response.text.strip()

            # Update memory with new interaction and track question
            self.update_context_window(user_id, question, response)

            return response
        except Exception as e:
            logging.error(f"Failed to query Gemini-1.5-Pro model: {e}")
            return f"Failed to query Gemini-1.5-Pro model: {e}"

async def run_gemini_with_memory(user_id:str, prompt:str) -> str:
    """
        Run Gemini Pro with context window tracking.
    """
    response = await LLMMemory().query(user_id, prompt)
    return response

# Test gemini with memory storage implementation
if __name__ == "__main__":
    test_user = "user_123" # simulated user id
    prompt = "What is the difference between a stack and a queue? Answer in one sentence."
    response = asyncio.run(run_gemini_with_memory(test_user, prompt))
    print(response)
