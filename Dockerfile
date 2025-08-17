# Базовый образ Python
FROM python:3.11-slim

# Обновляем пакеты и ставим нужные утилиты
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    megatools \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Скопировать requirements.txt и установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать весь проект
COPY . .

# Переменные окружения (чтобы Python не кешировал pyc)
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "ra_bot_gpt.py"]
