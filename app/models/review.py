from sqlalchemy import Column, Integer, Text, PrimaryKeyConstraint
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, index=True, autoincrement=True)
    product_id = Column(Integer, nullable=True)
    review_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    moderated_by = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)
    brand_id = Column(Integer, nullable=True)
    review_marketplace = Column(Text, nullable=True)    

    __table_args__ = (
        PrimaryKeyConstraint('review_id', 'review_marketplace', name='pk_review_id_review_marketplace'),
    )