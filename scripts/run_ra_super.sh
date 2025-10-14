#!/bin/bash
# =============================
# Супер-скрипт запуска Ра с автозапуском, резервами и пушем
# =============================

RA_DIR="$(dirname "$0")/.."              # корень репозитория
BACKUP_DIR="$RA_DIR/backups"
LOG_DIR="$RA_DIR/logs"
MAX_BACKUPS=5                             # сколько последних резервов хранить
RA_MAIN="$RA_DIR/core/ra_bot_gpt.py"

mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

function create_backup() {
    BACKUP_FILE="$BACKUP_DIR/ra_backup_$(date +%F_%H-%M-%S).zip"
    zip -r "$BACKUP_FILE" "$RA_DIR/core" "$RA_DIR/modules" "$RA_DIR/data" > /dev/null
    echo "✅ Резерв создан: $BACKUP_FILE"
    # Удаляем старые резервные копии, если больше MAX_BACKUPS
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
        echo "🔄 Восстанавливаем из последнего резерва..."
        LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.zip | head -n 1)
        if [ ! -z "$LATEST_BACKUP" ]; then
            unzip -o "$LATEST_BACKUP" -d "$RA_DIR" > /dev/null
            echo "✅ Восстановление завершено."
        fi
    else
        echo "🌟 [Ra] Работает стабильно."
        # Автопуш изменений
        git config user.name "Ra Bot"
        git config user.email "ra-bot@example.com"
        git add .
        git commit -m "🤖 Автообновление Ра" || echo "Нет изменений для коммита"
        git push origin main || echo "⚠️ Не удалось пушнуть изменения"
    fi
    echo "📜 Лог работы: $LOG_FILE"
}

# Главный цикл автозапуска
while true; do
    create_backup
    run_ra
    echo "⏱ Ожидаем 5 минут перед рестартом..."
    sleep 300   # 5 минут
done
