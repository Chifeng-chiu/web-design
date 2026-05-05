from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from database import Base


def utcnow():
    """取代棄用的 datetime.utcnow()，使用 timezone-aware 的 UTC 時間"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TradeType(enum.Enum):
    BUY = "buy"
    SELL = "sell"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String(500), nullable=False)

    trade_records = relationship("TradeRecord", back_populates="user")
    posts = relationship("Post", back_populates="user")


class TradeRecord(Base):
    __tablename__ = "trade_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_symbol = Column(String, nullable=False)
    trade_type = Column(Enum(TradeType), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    # 修正：改用 utcnow function 取代棄用的 datetime.utcnow
    trade_date = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="trade_records")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    # 修正：改用 utcnow function 取代棄用的 datetime.utcnow
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="posts")


class Comment(Base):
    """新增留言 model，讓使用者可以在文章下方留言交流"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    post = relationship("Post", back_populates="comments")
    user = relationship("User")


# 在 Post 補上 comments relationship
Post.comments = relationship("Comment", back_populates="post", order_by="Comment.created_at")