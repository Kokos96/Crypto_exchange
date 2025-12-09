import random
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models, database

# Створюємо таблиці при старті
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Початкова ціна (вона буде змінюватись)
CURRENT_BTC_PRICE = 50000.0

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(database.get_db)):
    # 1. Знаходимо гаманець
    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    # Якщо це перший запуск - даємо бонус 10к
    if not wallet:
        wallet = models.Wallet(username="trader_1", balance_usd=10000.0, balance_btc=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    # 2. Витягуємо останні 5 транзакцій (сортуємо від нових до старих)
    history = db.query(models.Transaction).filter(models.Transaction.user_id == wallet.id).order_by(desc(models.Transaction.timestamp)).limit(5).all()

    # 3. Генеруємо фейкові дані для графіку (10 точок)
    # Це імітація того, як ціна скакала останні 10 хвилин
    chart_data = [CURRENT_BTC_PRICE + random.uniform(-500, 500) for _ in range(10)]

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "wallet": wallet, 
        "price": round(CURRENT_BTC_PRICE, 2),
        "history": history,
        "chart_data": chart_data
    })

@app.post("/buy")
def buy_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    global CURRENT_BTC_PRICE
    # "Ринок реагує": ціна трохи змінюється після покупки
    CURRENT_BTC_PRICE += random.uniform(-100, 200)

    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    if wallet and wallet.balance_usd >= amount:
        # Рахуємо скільки бітка вийде
        btc_amount = amount / CURRENT_BTC_PRICE
        
        # Оновлюємо баланс
        wallet.balance_usd -= amount
        wallet.balance_btc += btc_amount
        
        # ЗАПИСУЄМО В ІСТОРІЮ
        new_tx = models.Transaction(
            user_id=wallet.id,
            amount_usd=amount,
            amount_btc=btc_amount,
            price_at_moment=CURRENT_BTC_PRICE
        )
        db.add(new_tx)
        
        db.commit()
    
    # Повертаємо користувача на головну сторінку
    return read_root(request, db)