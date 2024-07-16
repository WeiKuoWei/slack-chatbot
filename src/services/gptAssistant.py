import os
from openai import OpenAI
from dotenv import load_dotenv
from typing_extensions import override
from openai import AssistantEventHandler

load_dotenv()
KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=KEY)
response = None

class ChannelChatSummaryAssistant:
    def __init__(self):

        self.assistant = None
        self.vector_store = None
        self.thread = None

    def create_assistant(self):
        self.assistant = client.beta.assistants.create(
            name="Channel Chat Summary Assistant",
            instructions="You are an expert in summarizing historical conversations from discord channels. You have information of the time, author, channel name, etc.; use this information to provide insights on the historical conversations",
            model="gpt-3.5-turbo",
            tools=[{"type": "file_search"}]
        )

    def create_vector_store(self):
        self.vector_store = client.beta.vector_stores.create(name="Channel History")

    def upload_files(self, file_paths):
        for path in file_paths:
            if os.path.exists(path):
                print(f"File exists: {path}")
            else:
                print(f"File does not exist: {path}")

        file_streams = [open(path, "rb") for path in file_paths]

        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=self.vector_store.id, files=file_streams
        )

        print(file_batch.status)
        print(file_batch.file_counts)

    def update_assistant(self):
        self.assistant = client.beta.assistants.update(
            assistant_id=self.assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
        )

    def create_thread(self, content):
        self.thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        print(self.thread.tool_resources.file_search)

    class EventHandler(AssistantEventHandler):
        '''
        for some reason, adding the constructor to the class causes an error;
        will need to be fixed later on
        '''
        # def __init__(self, client):
        #     self.client = client
            
        # def __init__(self):
        #     self.outer_instance = None

        @override
        def on_text_created(self, text) -> None:
            print(f"\nassistant > ", end="", flush=True)

        @override
        def on_tool_call_created(self, tool_call):
            print(f"\nassistant > {tool_call.type}\n", flush=True)

        @override
        def on_message_done(self, message) -> None:
            message_content = message.content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(
                    annotation.text, f"[{index}]"
                )
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            # print(message_content.value)
            # print("\n".join(citations))
            global response 
            response = message_content.value
            # # save the variables
            # self.outer_instance.response = message_content.value

    def run_assistant(self, instructions):
        with client.beta.threads.runs.stream(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=instructions,
            # event_handler=self.EventHandler(self.client),
            event_handler=self.EventHandler(),
        ) as stream:
            stream.until_done()

    def process(self, file_paths, content, instructions):
        self.create_assistant()
        self.create_vector_store()
        self.upload_files(file_paths)
        self.update_assistant()
        self.create_thread(content)
        self.run_assistant(instructions)

        # return self.response

# Usage example:
def fetchAssistanceResponse(guild_id, channel_id, query):
    print(f"fetching response for guild_id: {guild_id}, channel_id: {channel_id}, query: {query}")
    assistant = ChannelChatSummaryAssistant()
    file_path = f"data/discord/{guild_id}/{channel_id}/messages.json"
    instructions = "Please address the user as Wei Kuo. The user has a premium account."
    try: 
        print(f"{type(query)}")
        assistant.process([file_path], query, instructions)

    except Exception as e:
        print(f"Error with general question: {e}")

    return response

'''
only for testing purpose; will be removed later

if __name__ == "__main__":
    response = fetchAssistanceResponse()
    print(response)

'''
