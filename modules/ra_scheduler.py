# modules/ra_scheduler.py
import asyncio
import logging


class RaScheduler:
    """
    Лёгкий планировщик cron-подобных задач.
    Используется как нервная система Ра.
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
            
    def add_task(self, coro, interval_seconds):
        """
        Добавляет задачу в планировщик.
        coro — асинхронная функция, interval_seconds — интервал запуска
        """
        self.jobs.append((coro, interval_seconds))
        logging.info(f"[RaScheduler] Добавлена задача {coro.__name__} каждые {interval_seconds} сек.")

    async def start(self):
        """
        Запуск всех задач в отдельные таски.
        """
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
        """
        Внутренний цикл для каждой задачи: выполняет её, ждёт интервал, повторяет.
        """
        while True:
            try:
                await coro()
            except Exception as e:
                logging.exception(f"[RaScheduler] Ошибка в задаче {coro.__name__}: {e}")
            await asyncio.sleep(interval)

    async def stop(self):
        """
        Остановка всех задач.
        """
        if not self._running:
            return

        self._running = False

        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

        logging.info("[RaScheduler] Все задачи остановлены.")

    def status(self):
        """
        Статус планировщика.
        """
        return {
            "jobs": len(self.jobs),
            "running_tasks": len(self._tasks),
            "is_running": self._running
        }

    # =====================================================
    # 🧠 Тик саморазвития Ра
    # =====================================================
    async def self_upgrade_tick(self):
        """
        Запускает тик саморазвития через thinker и upgrade_loop
        """
        if not self.thinker or not self.upgrade_loop:
            return

        try:
            proposal = await self.thinker.propose_upgrade()

            if not proposal:
                return

            logging.info("🧠 Ра предложил самоапгрейд")

            await self.upgrade_loop.apply_upgrade(
                target_file=proposal.get("file"),
                proposed_code=proposal.get("code"),
                approved=proposal.get("approved", False)
            )

        except Exception as e:
            logging.exception(f"[RaScheduler] Ошибка self_upgrade_tick: {e}")

    # =====================================================
    # 🛠 Обработка сообщений из мира
    # =====================================================
    async def process_world_message(self, message):
        """
        Реакция на внешние события
        """
        if "тревога" in str(message).lower():
            # тут пока заглушка, можно подключить свои задачи
            await self.schedule_immediate("stabilize")
            
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
        """
        Основной цикл планировщика, который нужно запускать как bg_task
        """
        # запускаем все задачи
        await self.start()
        logging.info("[RaScheduler] scheduler_loop запущен")
        while True:
            await asyncio.sleep(1)  # держим цикл живым
