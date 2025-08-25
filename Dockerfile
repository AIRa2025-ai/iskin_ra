# Базовый образ Python
FROM python:3.11-slim

# Обновляем пакеты и ставим нужные утилиты
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    wget \
    megatools \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Проверка, что FastAPI установлен (не критично для сборки)
RUN python -m pip show fastapi

# Запуск приложения через Uvicorn
CMD ["uvicorn", "ra_bot_gpt:app", "--host", "0.0.0.0", "--port", "8080"]
