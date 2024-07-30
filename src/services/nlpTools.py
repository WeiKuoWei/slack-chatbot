import re
import asyncio
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from concurrent.futures import ThreadPoolExecutor

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Function to perform preprocessing
def preprocess_text(text):
    # Tokenization
    tokens = word_tokenize(text)

    # Remove Noise
    cleaned_tokens = [re.sub(r'[^\w\s]', '', token) for token in tokens]

    # Remove empty strings
    cleaned_tokens = [token for token in cleaned_tokens if token]

    # other preprocessing steps
    cleaned_tokens = [token.lower() for token in cleaned_tokens]
    stop_words = set(stopwords.words('english'))
    cleaned_tokens = [token for token in cleaned_tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    cleaned_tokens = [lemmatizer.lemmatize(token) for token in cleaned_tokens]

    return cleaned_tokens

# Async function to run preprocessing in a thread
async def async_preprocess_text(text):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, preprocess_text, text)
        cleaned_text = ' '.join(result)

    return cleaned_text

async def preprocess_documents(documents):
    cleaned_documents = []
    for doc in documents:
        cleaned_doc = await async_preprocess_text(doc)
        cleaned_documents.append(cleaned_doc)
    return cleaned_documents

# # Example usage
# async def main():
#     synthetic_text = "Sample text."
#     cleaned_tokens = await async_preprocess_text(synthetic_text)
#     cleaned_text = ' '.join(cleaned_tokens)
#     print(cleaned_text)

# # Run the example
# asyncio.run(main())
