# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем утилиты (если реально нужны)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    wget \
    megatools \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости отдельно (чтобы кэшировалось)
COPY requirements.txt ./

# Устанавливаем зависимости
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем конфиг и проект
COPY bot_config.json ./
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск бота (aiogram polling)
CMD ["uvicorn", "ra_bot_gpt:app", "--host", "0.0.0.0", "--port", "8080"]

