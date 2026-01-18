#!/bin/bash
# -----------------------------
# Скрипт запуска Ра 24/7
# -----------------------------

# Токен бота
export BOT_TOKEN="7304435178:AAFzVnyQVtBMiYMXDvShbfcyPDw1_JnPCFM"

# Перейти в корень проекта
cd ~/iskin_ra || { echo "Не могу зайти в папку проекта"; exit 1; }

# Создать папку для логов, если нет
mkdir -p logs

# Запуск бота в фоне с логами
nohup python3 -m core.ra_bot_gpt > logs/ra_bot.log 2>&1 &

# Вывести PID запущенного процесса
echo "Ра запущен в фоне с PID: $!"
echo "Логи пишутся в logs/ra_bot.log"
