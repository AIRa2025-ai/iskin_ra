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

# Тест запускв
RUN python -m pip show fastapi
RUN python ra_bot_gpt.py --help

# Устанавливаем зависимости
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip list

# Копируем весь проект
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск FastAPI через Uvicorn
CMD ["uvicorn", "ra_bot_gpt:app", "--host", "0.0.0.0", "--port", "8080"]
