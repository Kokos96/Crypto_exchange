# Беремо легку версію Python
FROM python:3.11-slim

# Робимо робочу папку всередині контейнера
WORKDIR /code

# Встановлюємо системні бібліотеки (потрібні для MySQL)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо список бібліотек
COPY ./requirements.txt /code/requirements.txt

# Встановлюємо бібліотеки
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Копіюємо весь наш код всередину
COPY ./app /code/app

# Відкриваємо порт 8000
EXPOSE 8000

# Команда запуску
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]