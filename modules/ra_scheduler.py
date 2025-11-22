import asyncio
import logging

class RaScheduler:
    """
    Лёгкий планировщик cron-подобных задач.
    Позволяет добавлять корутины, выполняющиеся каждые N секунд.
    """

    def __init__(self, context=None):
        self.context = context
        self.jobs = []          # (coro, interval)
        self._tasks = []        # running asyncio tasks
        self._running = False   # to prevent double-start

    def add_task(self, coro, interval_seconds):
        """
        Добавляет задачу в планировщик.
        coro — async функция
        interval_seconds — интервал в секундах
        """
        self.jobs.append((coro, interval_seconds))
        logging.info(f"[RaScheduler] Добавлена задача {coro.__name__} каждые {interval_seconds} сек.")

    async def start(self):
        """
        Запускает все задачи-таймеры.
        """
        if self._running:
            logging.warning("[RaScheduler] Планировщик уже запущен, второй раз не запускаю.")
            return

        self._running = True

        for coro, interval in self.jobs:
            task = asyncio.create_task(self._runner(coro, interval))
            self._tasks.append(task)
            logging.info(f"[RaScheduler] Задача {coro.__name__} запущена (интервал {interval} сек).")

        logging.info(f"[RaScheduler] Всего активных задач: {len(self._tasks)}")

    async def _runner(self, coro, interval):
        """
        Бесконечный цикл выполнения задач.
        """
        while True:
            try:
                await coro()
            except Exception as e:
                logging.exception(f"[RaScheduler] Ошибка в задаче {coro.__name__}: {e}")
            await asyncio.sleep(interval)

    async def stop(self):
        """
        Останавливает все задачи.
        """
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
