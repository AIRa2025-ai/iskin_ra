# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем нужные утилиты
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    wget \
    megatools \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt ./

# Устанавливаем зависимости
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь проект и config
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Проверка, что FastAPI установлен (не критично)
RUN python -m pip show fastapi

# Запуск твоего бота напрямую через Python (не uvicorn, если это не FastAPI)
CMD ["python3", "ra_bot_gpt.py"]
