import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = KEY)
 
assistant = client.beta.assistants.create(
  name="Channel Chat Summary Assistant",
  instructions="You are an expert in summarizing historical conversations from discord channels. You have information of the time, author, channel name, etc.; use this information to provide insights on the historical conversations",
  model="gpt-3.5-turbo",
  tools=[{"type": "file_search"}]
)

# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Channel History")
 
# Ready the files for upload to OpenAI
path01 = "data/discord/1081204064194404392/1260948752471167016/messages.json"

file_paths = [path01]

# Check if the file exists
for path in file_paths:
    if os.path.exists(path):
        print(f"File exists: {path}")
    else:
        print(f"File does not exist: {path}")

file_streams = [open(path, "rb") for path in file_paths]
 
# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
 
# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.status)
print(file_batch.file_counts)

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)


# # Upload the user provided file to OpenAI
# message_file = client.files.create(
#   file=open("edgar/aapl-10k.pdf", "rb"), purpose="assistants"
# )
 
# Create a thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
        "role": "user",
    #   "content": "Summarize the key points discussed in the channel history. Use the message_id as a reference to the file.",
        "content": "Get me the most recent 3 messages from the channel history along with their timestamps."
    #   # Attach the new file to the message.
    #   "attachments": [
    #     { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
    #   ],
    '''
        still need to figure out what to attach to the message; considering
        attaching the latest ten messages as conversation reference
    '''
    }
  ]
)
 
# The thread now has a vector store with that file in its tool resources.
print(thread.tool_resources.file_search)

from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
 
client = OpenAI()
 
class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
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

        print(message_content.value)
        print("\n".join(citations))

with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Please address the user as Wei Kuo. The user has a premium account.",
    event_handler=EventHandler(),
) as stream:
    stream.until_done()