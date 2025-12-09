import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Якщо є змінна оточення (в Docker), беремо її. Якщо ні (на локалі) - беремо localhost
URL_DB = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@127.0.0.1:3306/crypto_exchange")

engine = create_engine(URL_DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()