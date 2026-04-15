from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContentSeriesPost(Base):
    __tablename__ = "content_series_post"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("content_series.id", ondelete="CASCADE"), nullable=False)
    # @note no unique constraint because there's a possibility that a post
    # could be associated to n series in the future.  This allows for that.
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)

    series = relationship("ContentSeries", back_populates="posts")
    post = relationship("Post")
