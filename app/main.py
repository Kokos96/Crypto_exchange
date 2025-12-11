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
    # 1. Знаходимо або створюємо гаманець
    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    if not wallet:
        wallet = models.Wallet(username="trader_1", balance_usd=10000.0, balance_btc=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    # 2. Витягуємо історію
    history = db.query(models.Transaction).filter(models.Transaction.user_id == wallet.id).order_by(desc(models.Transaction.timestamp)).limit(5).all()

    # 3. Генеруємо дані для графіку
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
    CURRENT_BTC_PRICE += random.uniform(-100, 200)

    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    # СУВОРІ ПЕРЕВІРКИ БАГУ (Fix 1)
    if amount <= 0:
        print("❌ Помилка: Сума має бути більша за нуль.")
        return read_root(request, db)

    if wallet and wallet.balance_usd >= amount:
        btc_amount = amount / CURRENT_BTC_PRICE
        
        wallet.balance_usd -= amount
        wallet.balance_btc += btc_amount
        
        new_tx = models.Transaction(
            user_id=wallet.id,
            amount_usd=amount,
            amount_btc=btc_amount,
            price_at_moment=CURRENT_BTC_PRICE
        )
        db.add(new_tx)
        db.commit()
    else:
        # Курс все одно змінюється, але транзакція не відбувається
        print("❌ Недостатньо USD для купівлі.") 

    return read_root(request, db)

# НОВА ФУНКЦІЯ: Продаж BTC
@app.post("/sell")
def sell_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    global CURRENT_BTC_PRICE
    CURRENT_BTC_PRICE += random.uniform(-200, 100) 

    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    # СУВОРІ ПЕРЕВІРКИ БАГУ (Fix 1)
    if amount <= 0:
        print("❌ Помилка: Сума має бути більша за нуль.")
        return read_root(request, db)
        
    btc_required = amount / CURRENT_BTC_PRICE 

    if wallet and wallet.balance_btc >= btc_required:
        
        wallet.balance_usd += amount 
        wallet.balance_btc -= btc_required
        
        new_tx = models.Transaction(
            user_id=wallet.id,
            amount_usd=-amount, 
            amount_btc=-btc_required, 
            price_at_moment=CURRENT_BTC_PRICE
        )
        db.add(new_tx)
        db.commit()
    else:
        # Курс все одно змінюється, але транзакція не відбувається
        print(f"❌ Недостатньо BTC для продажу. Потрібно: {btc_required}, є: {wallet.balance_btc}")

    return read_root(request, db)