from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models, database

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

print("⏳ Спроба підключення до БД...")
# Створюємо таблиці один раз тут
models.Base.metadata.create_all(bind=database.engine)
print("✅ БД підключена успішно! Таблиці створені.")

# Головна сторінка (Dashboard)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(database.get_db)):
    print("➡️ Запит отримано! Починаю шукати в базі...")
    
    # Шукаємо гаманець
    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    print(f"✅ Результат пошуку: {wallet}") # Додав вивід результату
    
    if not wallet:
        print("🔧 Створюю новий гаманець...")
        wallet = models.Wallet(username="trader_1", balance_usd=10000.0, balance_btc=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return templates.TemplateResponse("index.html", {"request": request, "wallet": wallet})

@app.post("/buy")
def buy_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    print(f"💰 Спроба купити на суму: {amount}")
    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    price_per_btc = 50000.0
    
    if wallet and wallet.balance_usd >= amount:
        wallet.balance_usd -= amount
        wallet.balance_btc += amount / price_per_btc
        db.commit()
        print("✅ Купівля успішна!")
    else:
        print("❌ Недостатньо грошей!")
    
    return templates.TemplateResponse("index.html", {"request": request, "wallet": wallet})