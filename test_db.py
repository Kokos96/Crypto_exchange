from sqlalchemy import create_engine, text

# Наш рядок підключення
DATABASE_URL = "mysql+pymysql://root:root@127.0.0.1:3306/crypto_exchange"

try:
    print("⏳ Пробую підключитися до бази...")
    engine = create_engine(DATABASE_URL)
    
    # Робимо тестовий запит
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 'Hello from MySQL!'"))
        print("✅ УСПІХ! База відповіла:", result.scalar())

except Exception as e:
    print("❌ ПОМИЛКА підключення:")
    print(e)