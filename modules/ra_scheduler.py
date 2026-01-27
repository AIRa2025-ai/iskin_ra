# modules/ra_scheduler.py
import asyncio
import logging

class RaScheduler:
    """
    Лёгкий планировщик cron-подобных задач.
    Используется как нервная система Ра.
    Теперь связан с RaThinker для тиков саморазвития и реакций на события.
    """

    def __init__(self, context=None, self_master=None, thinker=None, upgrade_loop=None, event_bus=None):
        self.context = context
        self.self_master = self_master
        self.thinker = thinker
        self.upgrade_loop = upgrade_loop
        self.event_bus = event_bus
        self.jobs = []          # список задач: (coro, interval)
        self._tasks = []        # внутренние asyncio-таски
        self._running = False   # флаг работы планировщика
        if self.event_bus:
            self.event_bus.subscribe("schedule", self.on_schedule)
            self.event_bus.subscribe("world", self.process_world_message)

    def add_task(self, coro, interval_seconds):
        self.jobs.append((coro, interval_seconds))
        logging.info(f"[RaScheduler] Добавлена задача {coro.__name__} каждые {interval_seconds} сек.")

    async def start(self):
        if self._running:
            logging.warning("[RaScheduler] Планировщик уже запущен.")
            return

        self._running = True
        for coro, interval in self.jobs:
            task = asyncio.create_task(self._runner(coro, interval))
            self._tasks.append(task)
            logging.info(f"[RaScheduler] Задача {coro.__name__} запущена (интервал {interval} сек).")
        logging.info(f"[RaScheduler] Всего активных задач: {len(self._tasks)}")

    async def _runner(self, coro, interval):
        while True:
            try:
                await coro()
            except Exception as e:
                logging.exception(f"[RaScheduler] Ошибка в задаче {coro.__name__}: {e}")
            await asyncio.sleep(interval)

    async def stop(self):
        if not self._running:
            return
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logging.info("[RaScheduler] Все задачи остановлены.")

    def status(self):
        return {
            "jobs": len(self.jobs),
            "running_tasks": len(self._tasks),
            "is_running": self._running
        }

    # =====================================================
    # 🛠 Обработка сообщений из мира
    # =====================================================
    async def process_world_message(self, message):
        if "тревога" in str(message).lower():
            await self.schedule_immediate("stabilize")
        # уведомляем thinker
        if self.thinker:
            await self.thinker.process_world_message(message)

    async def schedule_immediate(self, task_name):
        logging.info(f"[RaScheduler] Немедленная задача: {task_name}")

    # =====================================================
    # 🗓 Метод обработки события schedule
    # =====================================================
    async def on_schedule(self, event):
        logging.info(f"[RaScheduler] Получено событие schedule: {event}")
        for coro, interval in self.jobs:
            logging.info(f"[RaScheduler] Задача {coro.__name__} с интервалом {interval} сек.")

    # =====================================================
    # 🔄 Главный цикл планировщика (замена run_loop)
    # =====================================================
    async def scheduler_loop(self):
        await self.start()
        logging.info("[RaScheduler] scheduler_loop запущен")
        while True:
            # Добавляем тик саморазвития каждые 10 секунд
            if self.thinker and self.upgrade_loop:
                await self.upgrade_loop.tick()
            await asyncio.sleep(10)
