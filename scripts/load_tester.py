import requests
import threading
import time
import random
import sys
import signal

# --- НАЛАШТУВАННЯ ---
TARGET_URL = "http://localhost"
TOTAL_REQUESTS = 50000    
CONCURRENT_THREADS = 200  

counter = 0
errors = 0
lock = threading.Lock()
stop_event = threading.Event() # Прапорець для зупинки

def signal_handler(sig, frame):
    """Обробляє натискання Ctrl+C"""
    print("\n\n🛑 ОТРИМАНО КОМАНДУ СТОП! Завершуємо потоки...")
    stop_event.set()

def get_test_user_session():
    session = requests.Session()
    username = f"bot_{random.randint(1000, 999999)}"
    password = "password123"
    try:
        session.post(f"{TARGET_URL}/register", data={"username": username, "password": password})
        session.post(f"{TARGET_URL}/login", data={"username": username, "password": password})
        return session
    except:
        return None

def perform_attack(session):
    global counter, errors
    try:
        resp = session.post(f"{TARGET_URL}/buy", data={"amount": random.randint(10, 100)}, allow_redirects=False)
        with lock:
            if resp.status_code in [200, 302, 303]:
                counter += 1
                if counter % 100 == 0: 
                    print(f"🚀 Відправлено {counter} запитів...", end='\r')
            else:
                errors += 1
    except:
        with lock: errors += 1

def thread_worker():
    session = get_test_user_session()
    if not session: return

    while not stop_event.is_set(): # Перевіряємо, чи не натиснули стоп
        with lock:
            if counter + errors >= TOTAL_REQUESTS: break
        
        perform_attack(session)

def main():
    # Реєструємо обробник Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print(f"--- 💥 ПОЧАТОК АГРЕСИВНОГО ТЕСТУВАННЯ ---")
    print(f"Ціль: {TARGET_URL}")
    print(f"Потоків: {CONCURRENT_THREADS}")
    print(f"Щоб зупинити тест, натисни CTRL + C")
    print("-" * 40)
    
    threads = []
    for _ in range(CONCURRENT_THREADS):
        t = threading.Thread(target=thread_worker)
        t.daemon = True
        t.start()
        threads.append(t)

    # Чекаємо завершення потоків або зупинки
    for t in threads:
        t.join(timeout=0.1) # join з таймаутом, щоб працював Ctrl+C
        if stop_event.is_set():
            break

    while any(t.is_alive() for t in threads):
        if stop_event.is_set(): break
        time.sleep(0.1)

    print(f"\n--- 🏁 ЗАВЕРШЕНО: {counter} успішно, {errors} помилок ---")

if __name__ == "__main__":
    main()