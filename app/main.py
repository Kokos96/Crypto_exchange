import random
import os
import json
import time
import redis
from fastapi import FastAPI, Depends, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app import models, database

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

CURRENT_BTC_PRICE = 50000.0

# --- ОТРИМАННЯ ЮЗЕРА З КУКІВ ---
def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return db.query(models.Wallet).filter(models.Wallet.id == int(user_id)).first()

# --- СТОРІНКА ЛОГІНУ ---
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# --- РЕЄСТРАЦІЯ ---
@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    existing_user = db.query(models.Wallet).filter(models.Wallet.username == username).first()
    if existing_user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Такий користувач вже існує!"})
    
    new_wallet = models.Wallet(username=username, password=password)
    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(new_wallet.id))
    return response

# --- ВХІД ---
@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(models.Wallet).filter(models.Wallet.username == username).first()
    
    if not user or user.password != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Невірний логін або пароль"})
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

# --- ВИХІД ---
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response

# --- ГОЛОВНА ---
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(database.get_db)):
    wallet = get_current_user(request, db)
    if not wallet:
        return RedirectResponse(url="/login")
    
    history = db.query(models.Transaction).filter(models.Transaction.user_id == wallet.id).order_by(desc(models.Transaction.timestamp)).limit(10).all()
    chart_data = [CURRENT_BTC_PRICE + random.uniform(-500, 500) for _ in range(10)]

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "wallet": wallet, 
        "price": round(CURRENT_BTC_PRICE, 2),
        "history": history,
        "chart_data": chart_data
    })

# --- КУПІВЛЯ ---
@app.post("/buy")
def buy_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    wallet = get_current_user(request, db)
    if not wallet: return RedirectResponse(url="/login", status_code=303)

    global CURRENT_BTC_PRICE
    CURRENT_BTC_PRICE += random.uniform(-100, 200)
    
    if amount > 0 and wallet.balance_usd >= amount:
        task_payload = {
            "type": "BUY",
            "user_id": wallet.id,
            "amount_usd": amount,
            "current_price": CURRENT_BTC_PRICE
        }
        r.rpush('transaction_queue', json.dumps(task_payload))
        time.sleep(0.5) 
        
    return RedirectResponse(url="/", status_code=303)

# --- ПРОДАЖ ---
@app.post("/sell")
def sell_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    wallet = get_current_user(request, db)
    if not wallet: return RedirectResponse(url="/login", status_code=303)

    global CURRENT_BTC_PRICE
    CURRENT_BTC_PRICE += random.uniform(-200, 100) 
    
    btc_required = amount / CURRENT_BTC_PRICE 

    if amount > 0 and wallet.balance_btc >= btc_required:
        task_payload = {
            "type": "SELL",
            "user_id": wallet.id,
            "amount_usd": amount,
            "current_price": CURRENT_BTC_PRICE
        }
        r.rpush('transaction_queue', json.dumps(task_payload))
        time.sleep(0.5)

    return RedirectResponse(url="/", status_code=303)


# --- ЧІТ-КОД: ПОПОВНЕННЯ БАЛАНСУ ---
@app.post("/deposit")
def deposit_money(amount: float = Form(...), db: Session = Depends(database.get_db), request: Request = Request):
    # 1. Знаходимо поточного юзера
    wallet = get_current_user(request, db)
    if not wallet:
        return {"error": "Спочатку увійдіть в систему!"}
    
    # 2. Додаємо гроші
    wallet.balance_usd += amount
    db.commit()
    
    # 3. Повертаємо на головну
    return RedirectResponse(url="/", status_code=303)