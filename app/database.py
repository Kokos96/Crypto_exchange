from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Підключення до MySQL (який крутиться в Докері на порту 3306)
# Формат: mysql+pymysql://user:password@host:port/database_name
URL_DB = "mysql+pymysql://root:root@127.0.0.1:3306/crypto_exchange"

engine = create_engine(URL_DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Функція, щоб отримувати сесію БД в кожному запиті
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()