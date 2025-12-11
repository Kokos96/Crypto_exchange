import time
import subprocess

# Налаштування
SERVICE_NAME = "web"
MAX_CPU_THRESHOLD = 50.0  # Поріг навантаження для масштабування вгору
MIN_CPU_THRESHOLD = 10.0  # Поріг для зменшення
MAX_REPLICAS = 5
MIN_REPLICAS = 1

def get_current_replicas():
    """Рахує, скільки зараз запущено контейнерів web"""
    try:
        # Використовуємо список аргументів замість рядка (безпечніше для Windows)
        cmd = ["docker", "ps", "--format", "{{.Names}}"]
        # shell=False (за замовчуванням) - це те, що нам треба, щоб не залежати від CMD/Bash
        output = subprocess.check_output(cmd).decode()
        
        # Рахуємо рядки, де зустрічається 'web' (або ім'я твого сервісу)
        count = 0
        for line in output.splitlines():
            if "web" in line:
                count += 1
        return max(count, 1)
    except Exception as e:
        print(f"⚠️ Помилка зчитування реплік: {e}")
        return 1

def get_avg_cpu_usage():
    """Бере середнє навантаження CPU по всіх контейнерах web"""
    try:
        # КРОК 1: Отримуємо ID контейнерів окремою командою
        ps_cmd = ["docker", "ps", "-q", "-f", "name=web"]
        ids_output = subprocess.check_output(ps_cmd).decode().strip()
        
        if not ids_output:
            return 0.0
            
        container_ids = ids_output.split()

        # КРОК 2: Запитуємо статистику для цих ID
        # docker stats --no-stream --format "{{.CPUPerc}}" <id1> <id2> ...
        stats_cmd = ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}"] + container_ids
        output = subprocess.check_output(stats_cmd).decode()
        
        percentages = []
        for line in output.splitlines():
            clean_line = line.strip().replace('%', '')
            if clean_line:
                try:
                    percentages.append(float(clean_line))
                except ValueError:
                    continue
        
        if not percentages: return 0.0
        return sum(percentages) / len(percentages)

    except Exception as e:
        print(f"⚠️ Помилка отримання статистики CPU: {e}")
        return 0.0

def scale_service(replicas):
    """Виконує команду масштабування"""
    print(f"⚖️ Змінюю кількість контейнерів на: {replicas}...")
    # Тут використовуємо shell=True, бо docker-compose це часто зручніше запускати як рядок
    cmd = f"docker-compose up -d --scale {SERVICE_NAME}={replicas} --no-recreate"
    subprocess.run(cmd, shell=True)

def main():
    print("--- 🚀 AUTOSCALER ЗАПУЩЕНО (Windows Compatible) ---")
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
            time.sleep(10) # Чекаємо, поки нові контейнери запустяться

        # Логіка ЗМЕНШЕННЯ (SCALE DOWN)
        elif avg_cpu < MIN_CPU_THRESHOLD and current_replicas > MIN_REPLICAS:
            print("❄️ Навантаження впало. Економимо ресурси.")
            current_replicas -= 1
            scale_service(current_replicas)
        
        time.sleep(5)

if __name__ == "__main__":
    main()