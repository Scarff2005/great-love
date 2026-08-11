from sqlalchemy import Column, Integer, String, Text
from database import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default_user")
    category = Column(String, default="general")
    memory = Column(Text, nullable=False)