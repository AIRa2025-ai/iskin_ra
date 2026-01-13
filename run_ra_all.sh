#!/bin/bash

# Твой токен Telegram
export BOT_TOKEN="7304435178:AAFzVnyQVtBMiYMXDvShbfcyPDw1_JnPCFM"

# --- Поднимаем CORE в фоне ---
python3 run_ra_core.py &

# Даем CORE пару секунд для старта
sleep 3

# --- Поднимаем Telegram-бота из core ---
cd core || exit 1
python3 -m ra_bot_gpt
