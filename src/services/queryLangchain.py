import os, asyncio
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma

from utlis.config import OPENAI_API_KEY, DB_PATH

async def fetchGptResponse(query, data=[]):
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        max_tokens=500,
        openai_api_key=OPENAI_API_KEY
    )

    response = await asyncio.to_thread(
        llm.invoke,
        [
            ("system", f"You are a channel messages summarizer. You will be given 10 most relevant messages to the user query {str(data)}. Answer the user as detail as possible."),
            ("user", query)
        ]
    )
    print(response)
    return response.content

async def fetchLangchainResponse(query, channel_id):

    embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

    # Initialize the ChromaDB client and retriever
    client = Chroma(
        embedding_function=embedding_model,
        persist_directory=DB_PATH,  # Adjust this to your actual DB_PATH if needed
        collection_name=str(channel_id)
    )

    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        max_tokens=500,
        openai_api_key=OPENAI_API_KEY
    )

    try:
        # Initialize the RetrievalQA chain
        chatbot_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=client.as_retriever(search_kwargs={"k": 10}),
            verbose=True, 
            return_source_documents=True,

        )

        # Define the prompt template
        template = """
        respond as clearly as possible {query}?
        """

        prompt = PromptTemplate(
            input_variables=["query"],
            template=template,
        )

        # Run the query through the chatbot chain
        response = chatbot_chain.invoke(prompt.format(query=query))

        # print(response)
        return response

    except Exception as e:
        print(f"Error with fetching Langchain response: {e}")
        return "I'm sorry, I couldn't find an answer to that question."
