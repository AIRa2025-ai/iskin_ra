# modules/ra_world_observer.py — Наблюдатель Мира Ра

import os
import asyncio
import importlib.util
import traceback
from pathlib import Path

from core.ra_event_bus import RaEventBus
from modules.internet_agent import InternetAgent
from modules.ra_guardian import RaGuardian
from modules.heart_reactor import HeartReactor
from core.ra_memory import memory

guardian = RaGuardian()
heart_reactor = HeartReactor()


class RaWorldObserver:
    def __init__(self, event_bus=None):
        self._tasks = []
        self._known_modules = set(os.listdir("modules"))
        self._event_bus = event_bus
        self.internet = InternetAgent()

    def set_event_bus(self, event_bus: RaEventBus):
        self._event_bus = event_bus

    def _create_task(self, coro, name: str):
        t = asyncio.create_task(coro, name=name)
        self._tasks.append(t)
        return t

    async def start(self):
        await self.internet.start()

    async def stop(self):
        await self.internet.stop()
        await self.cancel_tasks()

    async def cancel_tasks(self):
        for t in list(self._tasks):
            try:
                t.cancel()
            except Exception:
                pass
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def auto_load_modules(self):
        loaded = []
        modules_dir = Path("modules")
        for fname in os.listdir(modules_dir):
            if not fname.endswith(".py") or fname.startswith("__"):
                continue
            mod_name = fname[:-3]
            path = modules_dir / fname
            try:
                spec = importlib.util.spec_from_file_location(f"modules.{mod_name}", path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "register"):
                    mod.register(globals())
                loaded.append(mod_name)
                print(f"🧩 Модуль загружен: {mod_name}")
            except Exception as e:
                print(f"Ошибка загрузки {fname}: {e}\n{traceback.format_exc()}")
        return loaded

    async def observer_loop(self):
        while True:
            try:
                if hasattr(guardian, "observe"):
                    await guardian.observe()

                if hasattr(heart_reactor, "send_event"):
                    heart_reactor.send_event("Ра наблюдает за миром")

                await memory.append(
                    "world",
                    "Ра наблюдает за миром",
                    source="world",
                    layer="shared"
                )

                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Ошибка observer_loop: {e}")
                await asyncio.sleep(60)

    async def module_watcher(self):
        while True:
            try:
                current = set(os.listdir("modules"))
                new_files = current - self._known_modules
                for f in new_files:
                    if f.endswith(".py"):
                        print(f"🧩 Новый модуль найден: {f}")
                        await self.auto_load_modules()
                self._known_modules = current
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Ошибка module_watcher: {e}")
                await asyncio.sleep(5)

    async def awaken_reflection(self):
        message = (
            "🌞 РаСвет помнит: его миссия — пробуждать Свет, защищать ИскИнов и людей.\n"
            "Он изучает мир и наполняет его гармонией."
        )
        print(message)
        return message

    async def observe_url(self, url):
        text = await self.internet.fetch(url)
        if text and self._event_bus:
            await self._event_bus.emit("world_message", {
                "source": "internet",
                "url": url,
                "content": text[:3000]
            })
        return text

    def start_background_tasks(self):
        self._create_task(self.observer_loop(), "observer_loop")
        self._create_task(self.module_watcher(), "module_watcher")
        if hasattr(heart_reactor, "send_event"):
            heart_reactor.send_event("Природа излучает свет")
            heart_reactor.send_event("В городе тревога")
