# modules/ra_scheduler.py
import asyncio
import logging

class RaScheduler:
    """
    Планировщик cron-подобных задач.
    """
    def __init__(self, context=None):
        self.context = context
        self.jobs = []

    def add_task(self, coro, interval_seconds):
        self.jobs.append((coro, interval_seconds))

    async def start(self):
        for coro, interval in self.jobs:
            asyncio.create_task(self._runner(coro, interval))

    async def _runner(self, coro, interval):
        while True:
            try:
                await coro()
            except Exception as e:
                logging.exception("RaScheduler job error")
            await asyncio.sleep(interval)

    async def stop(self):
        # TODO: можно хранить задачи в self._tasks и отменять их
        pass

    def status(self):
        return {"jobs": len(self.jobs)}
