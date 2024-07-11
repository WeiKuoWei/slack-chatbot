# modelsPydantic.py
from pydantic import BaseModel
from typing import List, Dict

class QueryRequest(BaseModel):
    query: str
    channel: str

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

class GeneralQuestion(BaseModel):
    query: str
