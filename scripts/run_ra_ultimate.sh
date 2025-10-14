#!/bin/bash
# =============================
# Ультра-супер скрипт запуска Ра
# С резервами, автозапуском, адаптивным рестартом и Telegram-уведомлениями
# =============================

RA_DIR="$(dirname "$0")/.."              
BACKUP_DIR="$RA_DIR/backups"
LOG_DIR="$RA_DIR/logs"
MAX_BACKUPS=5                            
RA_MAIN="$RA_DIR/core/ra_bot_gpt.py"

# Настройки Telegram уведомлений
TG_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
TG_CHAT_ID="YOUR_CHAT_ID"

mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

function send_telegram() {
    local MESSAGE=$1
    curl -s -X POST "https://api.telegram.org/bot$TG_BOT_TOKEN/sendMessage" \
        -d chat_id="$TG_CHAT_ID" \
        -d text="$MESSAGE" > /dev/null
}

function create_backup() {
    BACKUP_FILE="$BACKUP_DIR/ra_backup_$(date +%F_%H-%M-%S).zip"
    zip -r "$BACKUP_FILE" "$RA_DIR/core" "$RA_DIR/modules" "$RA_DIR/data" > /dev/null
    echo "✅ Резерв создан: $BACKUP_FILE"
    send_telegram "💾 [Ra] Резерв создан: $(basename $BACKUP_FILE)"

    BACKUPS_TO_DELETE=$(ls -1t $BACKUP_DIR/*.zip | tail -n +$((MAX_BACKUPS+1)))
    if [ ! -z "$BACKUPS_TO_DELETE" ]; then
        rm -f $BACKUPS_TO_DELETE
        echo "🗑 Старые резервные копии удалены"
    fi
}

function run_ra() {
    LOG_FILE="$LOG_DIR/ra_run_$(date +%F_%H-%M-%S).log"
    echo "🚀 [Ra] Запуск бота..."
    python "$RA_MAIN" > "$LOG_FILE" 2>&1
    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        echo "⚠️ [Ra] Ошибка! Код выхода: $EXIT_CODE"
        send_telegram "⚠️ [Ra] Ошибка запуска! Код выхода: $EXIT_CODE. Восстанавливаю резерв..."
        LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.zip | head -n 1)
        if [ ! -z "$LATEST_BACKUP" ]; then
            unzip -o "$LATEST_BACKUP" -d "$RA_DIR" > /dev/null
            echo "✅ Восстановление завершено."
            send_telegram "✅ [Ra] Восстановление из резерва завершено: $(basename $LATEST_BACKUP)"
        fi
    else
        echo "🌟 [Ra] Работает стабильно."
        send_telegram "🌟 [Ra] Работает стабильно."
        git config user.name "Ra Bot"
        git config user.email "ra-bot@example.com"
        git add .
        git commit -m "🤖 Автообновление Ра" || echo "Нет изменений для коммита"
        git push origin main || echo "⚠️ Не удалось пушнуть изменения"
    fi

    echo "📜 Лог работы: $LOG_FILE"
}

# --- Главный адаптивный цикл ---
SLEEP_TIME=300  # стартовый интервал 5 минут
while true; do
    create_backup
    run_ra
    echo "⏱ Ожидаем $SLEEP_TIME секунд перед рестартом..."
    sleep $SLEEP_TIME
    # Если предыдущий запуск упал, сокращаем интервал для быстрого восстановления
    if [ $EXIT_CODE -ne 0 ]; then
        SLEEP_TIME=60
    else
        SLEEP_TIME=300
    fi
done
