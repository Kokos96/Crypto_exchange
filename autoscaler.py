import time
import subprocess
import re

# Налаштування
SERVICE_NAME = "web"
MAX_CPU_THRESHOLD = 50.0  # Якщо більше 50% - масштабуємось
MIN_CPU_THRESHOLD = 10.0  # Якщо менше 10% - зменшуємось
MAX_REPLICAS = 5          # Максимум контейнерів
MIN_REPLICAS = 1          # Мінімум контейнерів

def get_current_replicas():
    """Рахує, скільки зараз запущено контейнерів web"""
    try:
        output = subprocess.check_output("docker ps --format '{{.Names}}'", shell=True).decode()
        # Шукаємо контейнери, які містять "crypto_exchange-web" (або як docker-compose їх назвав)
        count = len([line for line in output.split('\n') if "web" in line and line])
        return max(count, 1)
    except:
        return 1

def get_avg_cpu_usage():
    """Бере середнє навантаження CPU по всіх контейнерах web"""
    try:
        # Отримуємо статистику CPU без потоку (одноразово)
        cmd = "docker stats --no-stream --format '{{.CPUPerc}}' $(docker ps -q -f name=web)"
        output = subprocess.check_output(cmd, shell=True).decode()
        
        percentages = []
        for line in output.split('\n'):
            if line:
                # Видаляємо знак % і перетворюємо в число
                clean_line = re.sub(r'%', '', line).strip()
                percentages.append(float(clean_line))
        
        if not percentages: return 0.0
        return sum(percentages) / len(percentages)
    except Exception as e:
        print(f"Помилка отримання статистики: {e}")
        return 0.0

def scale_service(replicas):
    """Виконує команду масштабування"""
    print(f"⚖️ Змінюю кількість контейнерів на: {replicas}...")
    subprocess.run(f"docker-compose up -d --scale {SERVICE_NAME}={replicas} --no-recreate", shell=True)

def main():
    print("--- 🚀 AUTOSCALER ЗАПУЩЕНО ---")
    print(f"Слідкую за сервісом: {SERVICE_NAME}")
    
    current_replicas = get_current_replicas()
    
    while True:
        avg_cpu = get_avg_cpu_usage()
        print(f"📊 Поточне навантаження CPU: {avg_cpu:.2f}% | Контейнерів: {current_replicas}")

        # Логіка МАСШТАБУВАННЯ (SCALE UP)
        if avg_cpu > MAX_CPU_THRESHOLD and current_replicas < MAX_REPLICAS:
            print("🔥 Високе навантаження! Додаю потужності!")
            current_replicas += 1
            scale_service(current_replicas)
            time.sleep(10) # Даємо час на запуск

        # Логіка ЗМЕНШЕННЯ (SCALE DOWN)
        elif avg_cpu < MIN_CPU_THRESHOLD and current_replicas > MIN_REPLICAS:
            print("❄️ Навантаження впало. Економимо ресурси.")
            current_replicas -= 1
            scale_service(current_replicas)
        
        time.sleep(5) # Перевірка кожні 5 сек

if __name__ == "__main__":
    main()