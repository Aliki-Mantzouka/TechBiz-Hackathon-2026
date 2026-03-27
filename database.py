from sqlmodel import SQLModel, Field, create_engine
from typing import Optional

class HITLTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str
    context: str
    urgency: str
    status: str = "pending"
    callback_url: Optional[str] = None

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url)