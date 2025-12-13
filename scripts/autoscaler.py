import time
import subprocess
import os

# --- НАЛАШТУВАННЯ ---
SERVICE_NAME = "web"
MAX_CPU_THRESHOLD = 45.0
MIN_CPU_THRESHOLD = 10.0
MAX_REPLICAS = 5
MIN_REPLICAS = 1
CHECK_INTERVAL = 5

def get_active_containers():
    """Повертає список імен активних контейнерів"""
    try:
        cmd = ["docker", "ps", "--format", "{{.Names}}"]
        output = subprocess.check_output(cmd).decode()
        containers = [line for line in output.splitlines() if "web" in line]
        return containers
    except:
        return []

def get_avg_cpu_usage(container_ids):
    """Рахує середнє CPU по контейнерах"""
    if not container_ids: return 0.0
    try:
        # Отримуємо ID для команди stats
        ids_str = " ".join(container_ids)
        # --no-stream дає миттєвий знімок, а не потік
        cmd = f"docker stats --no-stream --format {{{{.CPUPerc}}}} {ids_str}"
        output = subprocess.check_output(cmd, shell=True).decode()
        
        percentages = []
        for line in output.splitlines():
            clean_line = line.strip().replace('%', '')
            try:
                percentages.append(float(clean_line))
            except:
                continue
        
        if not percentages: return 0.0
        return sum(percentages) / len(percentages)
    except:
        return 0.0

def scale_service(target_replicas):
    # Використовуємо subprocess.DEVNULL, щоб сховати спам від Докера
    cmd = f"docker-compose up -d --scale {SERVICE_NAME}={target_replicas} --no-recreate"
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print("\n" + "="*50)
    print(f"🚀 AUTOSCALER ЗАПУЩЕНО")
    print(f"🎯 Ціль: Тримати CPU між {MIN_CPU_THRESHOLD}% та {MAX_CPU_THRESHOLD}%")
    print("="*50 + "\n")
    
    current_replicas = 1
    
    while True:
        # 1. Отримуємо реальні контейнери
        containers = get_active_containers()
        real_count = len(containers)
        
        # Синхронізуємо змінну, якщо раптом руками щось змінили
        if real_count > 0:
            current_replicas = real_count

        # 2. Отримуємо навантаження
        avg_cpu = get_avg_cpu_usage(containers)

        # 3. Формуємо красивий рядок статусу
        status_symbol = "🟢" if avg_cpu < MAX_CPU_THRESHOLD else "🔴"
        print(f"{status_symbol} CPU: {avg_cpu:5.2f}% | Контейнерів: [ {real_count} ] ", end="")

        # 4. Логіка МАСШТАБУВАННЯ
        if avg_cpu > MAX_CPU_THRESHOLD and current_replicas < MAX_REPLICAS:
            print(f"\n\n🔥 ВИСОКЕ НАВАНТАЖЕННЯ! МАСШТАБУЮ ВГОРУ 📈")
            print(f"   Було: {current_replicas}  --->  Стане: {current_replicas + 1}")
            
            current_replicas += 1
            scale_service(current_replicas)
            
            print(f"   ✅ Готово. Чекаю 15 сек на стабілізацію...\n")
            time.sleep(15)
            continue # Пропускаємо sleep в кінці

        elif avg_cpu < MIN_CPU_THRESHOLD and current_replicas > MIN_REPLICAS:
            print(f"\n\n❄️ НАВАНТАЖЕННЯ ВПАЛО. МАСШТАБУЮ ВНИЗ 📉")
            print(f"   Було: {current_replicas}  --->  Стане: {current_replicas - 1}")
            
            current_replicas -= 1
            scale_service(current_replicas)
            
            print(f"   ✅ Готово. Зайвий контейнер видалено.\n")
            time.sleep(5)
        else:
            print("\r", end="") # Повертаємо каретку, щоб не спамити (оновлення рядка)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()