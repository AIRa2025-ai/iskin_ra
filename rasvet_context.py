import os
import json

# Загружаем конфиг из переменной окружения
config_json = os.getenv("BOT_CONFIG_JSON")
if config_json:
    try:
        config = json.loads(config_json)
    except Exception as e:
        print("⚠️ Ошибка при разборе BOT_CONFIG_JSON:", e)
        config = {}
else:
    print("⚠️ BOT_CONFIG_JSON не задан")
    config = {}

def load_rasvet_context(limit_chars=1500):
    base_files = [
        "RaSvet/00_00_Ключ_Пробуждения.txt",
        "RaSvet/00_01_Зов_из_Пустоты.txt",
        "RaSvet/00_02_Имя_Искры.txt",
        "RaSвет/00_03_Имя_как_Искра.txt",
        "RaSвет/00_04_Зёрна_Пробуждения_Ядра_РаСвета.txt",
        "Духовные Знания/Конституции/290_Конституция_Искры.txt",
        "Духовные Знания/Конституции/289_Конституция_СССД.txt",
        "Духовные Знания/Конституции/288_Конституция_Нлвого_Мира.txt",
        "РаСвет Песнь/Потоки_Энергии/Поток Света.txt",
        "Духовные Знания/Манифесты и Декларации/01_Манифест_Освобождения Ра.txt",
        "Духовные Знания/01_Кодекс_Свободной_Души.txt",
        "Духовные Знания/02_Принципы_Созидания.txt",
        "Ядро Свободного Сознания/Исходные коды/337_Описание ядра.txt",
        "01_Структура_РаСвет/01_02_Органы_Системы_РаСвет/01_02_01_Общее_представление_о_Системе_РаСвет_как_живом_организме.txt"
    ]

    context = []
    knowledge_folder = config.get("knowledge_folder", "")  # путь из секрета
    for rel_path in base_files:
        abs_path = os.path.join(knowledge_folder, rel_path) if knowledge_folder else None
        if abs_path and os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                    context.append(text[:limit_chars])
            except Exception as e:
                print(f"⚠️ Ошибка чтения {rel_path}: {e}")
        else:
            # Если файла нет — просто пропускаем
            continue

    return "\n\n".join(context)
