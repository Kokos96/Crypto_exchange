import requests
import threading
import time
import random

# --- НАЛАШТУВАННЯ ---
TARGET_URL = "http://localhost"  # Б'ємо в Nginx (порт 80)
TOTAL_REQUESTS = 1000            # Скільки всього запитів відправити
CONCURRENT_THREADS = 50          # Скільки "користувачів" одночасно (потоків)

# Глобальні змінні
counter = 0
errors = 0
lock = threading.Lock()

def get_test_user_session():
    """Реєструє бота і повертає Cookies (щоб нас пустило купувати)"""
    session = requests.Session()
    username = f"bot_{random.randint(1000, 99999)}"
    password = "password123"
    
    try:
        # 1. Реєстрація
        reg_data = {"username": username, "password": password}
        session.post(f"{TARGET_URL}/register", data=reg_data)
        
        # 2. Логін (на всяк випадок, хоча реєстрація логінить сама)
        session.post(f"{TARGET_URL}/login", data=reg_data)
        
        print(f"Бот {username} створений і готовий до тестування.")
        return session
    except Exception as e:
        print(f"Помилка реєстрації бота: {e}")
        return None

def perform_attack(session, request_id):
    """Один запит на покупку"""
    global counter, errors
    
    amount = random.randint(10, 100)
    
    try:
        # Відправляємо запит на КУПІВЛЮ через Nginx
        response = session.post(
            f"{TARGET_URL}/buy", 
            data={"amount": amount},
            allow_redirects=False # Щоб не вантажити HTML, нам головне факт запиту
        )
        
        status = response.status_code
        
        with lock:
            if status in [200, 302, 303]:
                counter += 1
                # Вивід кожні 50 запитів
                if counter % 50 == 0:
                    print(f"Відправлено {counter} транзакцій... (Nginx працює)")
            else:
                errors += 1
                print(f"Помилка: {status}")
                
    except Exception as e:
        with lock:
            errors += 1
        # print(f"Connection Error: {e}")

def thread_worker(session):
    """Потік, який шле запити, поки не досягнемо ліміту"""
    while True:
        with lock:
            current_count = counter + errors
            if current_count >= TOTAL_REQUESTS:
                break
        perform_attack(session, current_count)
        time.sleep(0.05) # Маленька пауза, щоб не покласти твій ноут повністю

def main():
    print(f"--- ПОЧАТОК НАВАНТАЖУВАЛЬНОГО ТЕСТУВАННЯ ---")
    print(f"Ціль: {TARGET_URL} (Nginx Load Balancer)")
    print(f"Запитів: {TOTAL_REQUESTS}")
    print(f"Потоків: {CONCURRENT_THREADS}")
    print("------------------------------------------------")

    # 1. Отримуємо сесію (реєструємо одного юзера, який буде все купувати)
    session = get_test_user_session()
    if not session:
        return

    # 2. Запускаємо потоки
    threads = []
    start_time = time.time()
    
    print("Тестування почалося. Переглядайте логи Docker.")
    
    for _ in range(CONCURRENT_THREADS):
        t = threading.Thread(target=thread_worker, args=(session,))
        t.daemon = True
        t.start()
        threads.append(t)

    # 3. Чекаємо завершення
    for t in threads:
        t.join()

    end_time = time.time()
    duration = end_time - start_time
    rps = counter / duration

    print("\n--- ТЕСТ ЗАВЕРШЕНО ---")
    print(f"Успішних запитів: {counter}")
    print(f"Помилок: {errors}")
    print(f"Час: {duration:.2f} сек")
    print(f"Швидкість: {rps:.2f} запитів/сек")

if __name__ == "__main__":
    main()