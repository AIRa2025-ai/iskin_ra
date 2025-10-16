# modules/my_module.py
class MyModule:
    def __init__(self, context):
        self.context = context  # ссылка на менеджер/манифест/логгер

    async def start(self): pass   # запустить таски/инициализация
    async def stop(self): pass    # корректная остановка
    def status(self) -> dict:     # краткая инфа
        return {"ok": True}
