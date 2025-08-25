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

# Скопировать requirements.txt и установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Скопировать весь проект
COPY . .

# Переменные окружения (чтобы Python не кешировал pyc и писал логи сразу)
ENV PYTHONUNBUFFERED=1

# Запуск FastAPI через Uvicorn
CMD ["uvicorn", "ra_bot_gpt:app", "--host", "0.0.0.0", "--port", "8080"]
