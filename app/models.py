from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100))  # <--- НОВЕ ПОЛЕ
    balance_usd = Column(Float, default=10000.0)
    balance_btc = Column(Float, default=0.0)
    
    transactions = relationship("Transaction", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("wallets.id"))
    amount_usd = Column(Float)
    amount_btc = Column(Float)
    price_at_moment = Column(Float) 
    timestamp = Column(DateTime, default=datetime.utcnow)

    owner = relationship("Wallet", back_populates="transactions")