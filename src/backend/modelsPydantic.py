# modelsPydantic.py
from pydantic import BaseModel
from typing import List, Dict

class Message(BaseModel):
    channel_id: int
    channel_name: str
    message_id: int
    author: str
    content: str
    timestamp: str

class UpdateRequest(BaseModel):
    guild_id: int
    channels: List[Dict]
    messages: List[Message]

class QueryRequest(BaseModel):
    guild_id: int
    channel_id: str
    query: str


class QueryResponse(BaseModel):
    answer: str
