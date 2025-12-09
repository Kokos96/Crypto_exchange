from sqlalchemy import Column, Integer, Float, String
from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    balance_usd = Column(Float, default=10000.0)  # Стартовий баланс 10к
    balance_btc = Column(Float, default=0.0)