import random
import os
import json # Для перетворення даних у формат для черги
import redis # Для роботи з Redis

from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models, database

# Ініціалізація підключення до REDIS
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

CURRENT_BTC_PRICE = 50000.0

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(database.get_db)):
    # ... (Частина, що тільки ЧИТАЄ дані, залишається синхронною) ...
    
    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    if not wallet:
        wallet = models.Wallet(username="trader_1", balance_usd=10000.0, balance_btc=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    history = db.query(models.Transaction).filter(models.Transaction.user_id == wallet.id).order_by(desc(models.Transaction.timestamp)).limit(5).all()
    chart_data = [CURRENT_BTC_PRICE + random.uniform(-500, 500) for _ in range(10)]

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "wallet": wallet, 
        "price": round(CURRENT_BTC_PRICE, 2),
        "history": history,
        "chart_data": chart_data
    })

# НОВИЙ АСИНХРОННИЙ ПУБЛІКАТОР: КУПІВЛЯ
@app.post("/buy")
def buy_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    global CURRENT_BTC_PRICE
    CURRENT_BTC_PRICE += random.uniform(-100, 200)

    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    if amount <= 0: return read_root(request, db)

    if wallet and wallet.balance_usd >= amount:
        # 1. СТВОРЮЄМО ЗАВДАННЯ ДЛЯ ЧЕРГИ
        task_payload = {
            "type": "BUY",
            "user_id": wallet.id,
            "amount_usd": amount,
            "current_price": CURRENT_BTC_PRICE
        }
        
        # 2. ПУБЛІКУЄМО В REDIS
        r.rpush('transaction_queue', json.dumps(task_payload)) # <--- Ключова дія!
        
    # Після публікації миттєво повертаємо користувача на головну. 
    # Транзакція в БД відбудеться пізніше.
    return read_root(request, db)

# НОВИЙ АСИНХРОННИЙ ПУБЛІКАТОР: ПРОДАЖ
@app.post("/sell")
def sell_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    global CURRENT_BTC_PRICE
    CURRENT_BTC_PRICE += random.uniform(-200, 100) 

    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    if amount <= 0: return read_root(request, db)
        
    btc_required = amount / CURRENT_BTC_PRICE 

    if wallet and wallet.balance_btc >= btc_required:
        # 1. СТВОРЮЄМО ЗАВДАННЯ ДЛЯ ЧЕРГИ
        task_payload = {
            "type": "SELL",
            "user_id": wallet.id,
            "amount_usd": amount,
            "current_price": CURRENT_BTC_PRICE
        }
        
        # 2. ПУБЛІКУЄМО В REDIS
        r.rpush('transaction_queue', json.dumps(task_payload)) # <--- Ключова дія!

    return read_root(request, db)