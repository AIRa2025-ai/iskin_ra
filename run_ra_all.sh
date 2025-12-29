#!/bin/bash

# Твой токен Telegram
export BOT_TOKEN="7304435178:AAFzKcVaxceCoIcJ5F2Mys6EYB21ABmfQGM"

# Запускаем CORE в фоне
python3 run_ra_core.py &

# Даем CORE пару секунд, чтобы поднялся
sleep 3

# Запускаем Telegram-бота
python3 -m core.ra_bot_gpt

# Всё, бот и CORE теперь работают вместе
