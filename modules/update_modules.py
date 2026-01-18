# update_modules.py
import asyncio
from core.ra_self_master import RaSelfMaster
from modules.ra_logger import RaLogger
from modules.ra_memory import RaMemory
from modules.ra_heart import RaHeart
from modules.gpt_module import GPTModule

async def main():
    # Создаем ядро Ра
    ra = RaSelfMaster(
        identity=None,
        gpt_module=GPTModule(),
        memory=RaMemory(),
        heart=RaHeart(),
        logger=RaLogger()
    )

    # Пробуждаем систему
    msg = await ra.awaken()
    print(msg)

    # Автоподключаем модули
    await ra.auto_activate_modules()

    # Запуск цикла саморазвития уже внутри RaSelfMaster
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
