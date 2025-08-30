# === Базовый образ Python 3.11 slim ===
FROM python:3.11-slim

# Устанавливаем необходимые утилиты
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости отдельно, чтобы использовать кэширование
COPY requirements.txt ./ 

# Устанавливаем зависимости Python
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Указываем порт для Fly.io
EXPOSE 8080

# Запуск FastAPI через Python-модуль uvicorn
CMD ["python", "-m", "uvicorn", "ra_bot_gpt:app", "--host", "0.0.0.0", "--port", "8080"]
