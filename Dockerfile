# --- Базовый Python образ ---
FROM python:3.11-slim

# --- Устанавливаем рабочую директорию ---
WORKDIR /app

# --- Работа с Мега ---
RUN pip install mega.py

# --- Копируем проект в контейнер ---
COPY . /app

# --- Устанавливаем системные зависимости ---
RUN apt-get update && \
    apt-get install -y git curl && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir aiohttp gitpython python-dotenv watchdog

# Внутри контейнера создаём папку для памяти
RUN mkdir -p /app/memory /app/logs
VOLUME ["/app/memory", "/app/logs"]

# --- Копируем скрипт автообновления модулей ---
COPY scripts/update_modules.py /app/scripts/update_modules.py

# --- Копируем скрипт авто-перезапуска бота ---
COPY scripts/run_bot.py /app/scripts/run_bot.py

# --- Открываем порт для вебхуков или API (если нужно) ---
EXPOSE 8080

# --- Команда запуска: сначала обновляем модули, потом запускаем бот с автоперезапуском ---
CMD ["python", "/app/scripts/run_bot.py"]
