import random
import os
import json
import time  # <--- Додано
import redis

# Додали RedirectResponse
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models, database

# Ініціалізація REDIS
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

CURRENT_BTC_PRICE = 50000.0

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(database.get_db)):
    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    if not wallet:
        wallet = models.Wallet(username="trader_1", balance_usd=10000.0, balance_btc=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    # Сортуємо: нові зверху
    history = db.query(models.Transaction).filter(models.Transaction.user_id == wallet.id).order_by(desc(models.Transaction.timestamp)).limit(10).all()
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
    
    if amount > 0 and wallet and wallet.balance_usd >= amount:
        task_payload = {
            "type": "BUY",
            "user_id": wallet.id,
            "amount_usd": amount,
            "current_price": CURRENT_BTC_PRICE
        }
        r.rpush('transaction_queue', json.dumps(task_payload))
        
        # Чекаємо, щоб воркер встиг обробити перед перезавантаженням
        time.sleep(0.5) 
        
    # Redirect замість render (Фікс F5)
    return RedirectResponse(url="/", status_code=303)

@app.post("/sell")
def sell_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
    global CURRENT_BTC_PRICE
    CURRENT_BTC_PRICE += random.uniform(-200, 100) 

    wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
    btc_required = amount / CURRENT_BTC_PRICE 

    if amount > 0 and wallet and wallet.balance_btc >= btc_required:
        task_payload = {
            "type": "SELL",
            "user_id": wallet.id,
            "amount_usd": amount,
            "current_price": CURRENT_BTC_PRICE
        }
        r.rpush('transaction_queue', json.dumps(task_payload))
        
        time.sleep(0.5)

    # Redirect замість render (Фікс F5)
    return RedirectResponse(url="/", status_code=303)












# import random
# import os
# import json 
# import time  # <--- 1. Додали time для паузи
# import redis 

# # <--- 2. Додали RedirectResponse
# from fastapi import FastAPI, Depends, Request, Form
# from fastapi.responses import HTMLResponse, RedirectResponse 
# from fastapi.templating import Jinja2Templates
# from sqlalchemy.orm import Session
# from sqlalchemy import desc

# from app import models, database

# # ... (Ініціалізація Redis і DB без змін) ...
# REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
# r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

# models.Base.metadata.create_all(bind=database.engine)

# app = FastAPI()
# templates = Jinja2Templates(directory="app/templates")

# CURRENT_BTC_PRICE = 50000.0

# @app.get("/", response_class=HTMLResponse)
# def read_root(request: Request, db: Session = Depends(database.get_db)):
#     # ... (Твій код читання гаманця) ...
#     wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
#     if not wallet:
#         wallet = models.Wallet(username="trader_1", balance_usd=10000.0, balance_btc=0.0)
#         db.add(wallet)
#         db.commit()
#         db.refresh(wallet)
    
#     # Сортуємо транзакції: найновіші зверху
#     history = db.query(models.Transaction).filter(models.Transaction.user_id == wallet.id).order_by(desc(models.Transaction.timestamp)).limit(10).all()
#     chart_data = [CURRENT_BTC_PRICE + random.uniform(-500, 500) for _ in range(10)]

#     return templates.TemplateResponse("index.html", {
#         "request": request, 
#         "wallet": wallet, 
#         "price": round(CURRENT_BTC_PRICE, 2),
#         "history": history,
#         "chart_data": chart_data
#     })

# @app.post("/buy")
# def buy_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
#     global CURRENT_BTC_PRICE
#     CURRENT_BTC_PRICE += random.uniform(-100, 200)

#     wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
#     if amount <= 0: 
#         # Якщо помилка - повертаємо на головну через редірект
#         return RedirectResponse(url="/", status_code=303)

#     if wallet and wallet.balance_usd >= amount:
#         task_payload = {
#             "type": "BUY",
#             "user_id": wallet.id,
#             "amount_usd": amount,
#             "current_price": CURRENT_BTC_PRICE
#         }
#         r.rpush('transaction_queue', json.dumps(task_payload))
        
#         # ХАК ДЛЯ КУРСОВОЇ: 
#         # Чекаємо 0.5 сек, щоб worker встиг записати в БД, і ми побачили це в історії
#         time.sleep(0.5) 
        
#     # <--- 3. ГОЛОВНИЙ ФІКС: RedirectResponse замість read_root
#     # status_code=303 змушує браузер зробити GET запит замість повторного POST
#     return RedirectResponse(url="/", status_code=303)

# @app.post("/sell")
# def sell_btc(request: Request, amount: float = Form(...), db: Session = Depends(database.get_db)):
#     global CURRENT_BTC_PRICE
#     CURRENT_BTC_PRICE += random.uniform(-200, 100) 

#     wallet = db.query(models.Wallet).filter(models.Wallet.username == "trader_1").first()
    
#     if amount <= 0: 
#         return RedirectResponse(url="/", status_code=303)
        
#     btc_required = amount / CURRENT_BTC_PRICE 

#     if wallet and wallet.balance_btc >= btc_required:
#         task_payload = {
#             "type": "SELL",
#             "user_id": wallet.id,
#             "amount_usd": amount,
#             "current_price": CURRENT_BTC_PRICE
#         }
#         r.rpush('transaction_queue', json.dumps(task_payload))
        
#         # Чекаємо воркера
#         time.sleep(0.5)

#     # <--- 4. Теж редірект
#     return RedirectResponse(url="/", status_code=303)