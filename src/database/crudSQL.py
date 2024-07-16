import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from utlis.config import DB_URL

Base = declarative_base()

# Define the ChatHistory model
class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    channel_id = sa.Column(sa.String, index=True)
    channel_name = sa.Column(sa.String)
    message_id = sa.Column(sa.String, unique=True, index=True)
    author = sa.Column(sa.String)
    content = sa.Column(sa.Text)
    timestamp = sa.Column(sa.String)
    embedding = sa.Column(sa.PickleType)

# Initialize database connection
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

class CRUD():
    def __init__(self):
        self.db = SessionLocal()

    def save_chat_history(self, chat_history):
        try:
            for chat in chat_history:
                chat_record = ChatHistory(
                    channel_id=str(chat['channel_id']),
                    channel_name=chat['channel_name'],
                    message_id=str(chat['message_id']),
                    author=chat['author'],
                    content=chat['content'],
                    timestamp=chat['timestamp'],
                    embedding=chat['embedding']
                )
                self.db.add(chat_record)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error saving chat history: {e}")

    def retrieve_relevant_history(self, channel_id, query_embedding, top_k=10):
        try:
            stmt = select(ChatHistory).where(ChatHistory.channel_id == str(channel_id))
            results = self.db.execute(stmt).scalars().all()

            # Calculate similarity (e.g., cosine similarity) between query_embedding and stored embeddings
            # This example assumes you have a function `calculate_similarity` defined elsewhere
            similar_chats = sorted(
                results,
                key=lambda chat: calculate_similarity(chat.embedding, query_embedding),
                reverse=True
            )[:top_k]

            return similar_chats
        except SQLAlchemyError as e:
            print(f"Error retrieving relevant history: {e}")
            return []

    def close(self):
        self.db.close()

def calculate_similarity(embedding1, embedding2):
    # Define your similarity calculation here (e.g., cosine similarity)
    pass
