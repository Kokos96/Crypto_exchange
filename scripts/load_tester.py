import requests
import threading
import time
import random

TARGET_URL = "http://localhost"
TOTAL_REQUESTS = 1000
CONCURRENT_THREADS = 50

counter = 0
errors = 0
lock = threading.Lock()

def get_test_user_session():
    session = requests.Session()
    username = f"bot_{random.randint(1000, 99999)}"
    password = "password123"
    try:
        session.post(f"{TARGET_URL}/register", data={"username": username, "password": password})
        session.post(f"{TARGET_URL}/login", data={"username": username, "password": password})
        print(f" Бот {username} готовий!")
        return session
    except:
        print(" Помилка реєстрації")
        return None

def perform_attack(session):
    global counter, errors
    try:
        resp = session.post(f"{TARGET_URL}/buy", data={"amount": random.randint(10, 100)}, allow_redirects=False)
        with lock:
            if resp.status_code in [200, 302, 303]:
                counter += 1
                if counter % 50 == 0: print(f" {counter} транзакцій відправлено...")
            else:
                errors += 1
    except:
        with lock: errors += 1

def thread_worker(session):
    while True:
        with lock:
            if counter + errors >= TOTAL_REQUESTS: break
        perform_attack(session)
        time.sleep(0.05)

def main():
    print(f"---  ПОЧАТОК ТЕСТУВАННЯ ---")
    session = get_test_user_session()
    if not session: return

    threads = []
    for _ in range(CONCURRENT_THREADS):
        t = threading.Thread(target=thread_worker, args=(session,))
        t.daemon = True
        t.start()
        threads.append(t)

    for t in threads: t.join()

    print(f"\n---  ЗАВЕРШЕНО: {counter} успішно, {errors} помилок ---")

if __name__ == "__main__":
    main()