import os
import json
import time
import redis
from sqlalchemy.orm import Session
from app import models, database # Імпортуємо наші моделі та підключення до БД

# 1. Ініціалізація REDIS
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
QUEUE_KEY = 'transaction_queue'

# Функція для отримання сесії БД (потрібна для Worker'а)
def get_db_session():
    db = database.SessionLocal()
    try:
        return db
    finally:
        db.close()

# 2. ФУНКЦІЯ ОБРОБКИ ЗАВДАННЯ
def process_transaction(db: Session, task_payload):
    tx_type = task_payload['type']
    user_id = task_payload['user_id']
    amount_usd = task_payload['amount_usd']
    price = task_payload['current_price']
    
    wallet = db.query(models.Wallet).filter(models.Wallet.id == user_id).first()
    
    if not wallet:
        print(f"Worker Error: Гаманець {user_id} не знайдено.")
        return

    # --- ЛОГІКА КУПІВЛІ/ПРОДАЖУ ---
    
    if tx_type == "BUY":
        if wallet.balance_usd >= amount_usd:
            btc_amount = amount_usd / price
            wallet.balance_usd -= amount_usd
            wallet.balance_btc += btc_amount
            
            new_tx = models.Transaction(user_id=user_id, amount_usd=amount_usd, amount_btc=btc_amount, price_at_moment=price)
            db.add(new_tx)
            db.commit()
            print(f"Worker: Купівля виконана для {amount_usd} USD.")
            return True
        
    elif tx_type == "SELL":
        btc_required = amount_usd / price
        if wallet.balance_btc >= btc_required:
            wallet.balance_usd += amount_usd
            wallet.balance_btc -= btc_required
            
            new_tx = models.Transaction(user_id=user_id, amount_usd=-amount_usd, amount_btc=-btc_required, price_at_moment=price)
            db.add(new_tx)
            db.commit()
            print(f"Worker: Продаж виконаний для {amount_usd} USD.")
            return True

    # Якщо недостатньо коштів, завдання просто пропускається
    print(f"Worker: Транзакція {tx_type} не виконана (Недостатньо коштів).")
    return False

# 3. ОСНОВНИЙ ЦИКЛ СПОЖИВАННЯ
if __name__ == "__main__":
    print("--- WORKER SERVICE STARTED, Очікування завдань у черзі ---")
    
    # Переконаємося, що таблиці існують перед початком роботи
    db_init = get_db_session()
    models.Base.metadata.create_all(bind=db_init.bind)
    db_init.close()
    
    while True:
        # blpop: Блокує потік і чекає, поки з'явиться нове завдання
        task = r.blpop(QUEUE_KEY, timeout=1) 
        
        if task:
            queue_name, raw_data = task
            try:
                task_payload = json.loads(raw_data)
                
                db_session = get_db_session()
                process_transaction(db_session, task_payload)
                db_session.close()

            except Exception as e:
                print(f" Worker CRITICAL ERROR: {e}")
        else:
            # Якщо завдань немає, робимо паузу, щоб не завантажувати процесор
            time.sleep(0.5)