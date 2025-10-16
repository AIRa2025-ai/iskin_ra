# modules/ra_scheduler.py
import asyncio
class RaScheduler:
    def __init__(self, context):
        self.context = context
        self.jobs = []

    def add_task(self, coro, interval_seconds):
        self.jobs.append((coro, interval_seconds))

    async def start(self):
        async def runner(coro, sec):
            while True:
                try:
                    await coro()
                except Exception:
                    pass
                await asyncio.sleep(sec)
        for coro, sec in self.jobs:
            asyncio.create_task(runner(coro, sec))
