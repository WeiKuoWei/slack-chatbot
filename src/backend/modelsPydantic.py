# modelsPydantic.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class QueryRequest(BaseModel):
    guild_id: int
    channel_id: int
    query: str

class QueryResponse(BaseModel):
    answer: str

class Message(BaseModel):
    channel_id: int
    channel_name: str
    message_id: int
    author: str
    author_id: int
    content: str
    timestamp: str
    profanity_score: float

class UpdateChatHistory(BaseModel):
    all_messages: Dict[int, List[Message]]

class UpdateGuildInfo(BaseModel):
    guild_id: int
    guild_name: str
    guild_purpose: Optional[str] = "null"
    number_of_channels: int
    number_of_members: int
    profanity_score: Optional[float] = 0.0

class UpdateChannelInfo(BaseModel):
    channel_id: int
    guild_id: int
    channel_name: str
    channel_purpose: Optional[str] = "null"
    number_of_messages: int
    number_of_members: int
    last_message_timestamp: Optional[str] = "null"
    first_message_timestamp: Optional[str] = "null"
    profanity_score: Optional[float] = 0.0

class UpdateMemberInfo(BaseModel):
    user_id: int
    channel_id: int
    channel_list_id: str
    user_name: str
    user_description: Optional[str] = "null"
    message_sent: int
    profanity_score: Optional[float] = 0.0

class UpdateChannelList(BaseModel):
    user_id: int
    user_name: str
    guild_id: int
    channel_ids: List[int]
    