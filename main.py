from fastapi import FastAPI

app = FastAPI()

# Це наша база даних в оперативній пам'яті (поки що без справжньої БД)
fake_wallet = {
    "user_id": 1,
    "usd_balance": 10000.0,  # У нас є 10 тисяч доларів
    "btc_balance": 0.0       # І 0 біткоїнів
}

@app.get("/")
def read_root():
    return {"message": "Вітаємо на біржі! Система працює."}

@app.get("/wallet")
def get_wallet():
    """Показати баланс"""
    return fake_wallet

@app.post("/buy/{amount}")
def buy_btc(amount: float):
    """Купити біткоїн на суму amount доларів"""
    price_per_btc = 50000.0 # Уявимо, що біткоїн коштує 50к
    
    if fake_wallet["usd_balance"] >= amount:
        # Списуємо долари
        fake_wallet["usd_balance"] -= amount
        # Нараховуємо біткоїни
        btc_bought = amount / price_per_btc
        fake_wallet["btc_balance"] += btc_bought
        
        return {"status": "success", "new_balance": fake_wallet}
    else:
        return {"status": "error", "message": "Недостатньо грошей!"}