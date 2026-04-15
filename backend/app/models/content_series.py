from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContentSeries(Base):
    __tablename__ = "content_series"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    root_scheduled_at = Column(DateTime(timezone=True), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="content_series")
    posts = relationship("ContentSeriesPost", back_populates="series", cascade="all, delete-orphan")
