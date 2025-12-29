# core/ra_ipc.py — простой TCP-сервер для RaContext
import asyncio
import json
import logging

class RaIPCServer:
    def __init__(self, host="127.0.0.1", port=8765, context=None):
        self.host = host
        self.port = port
        self.context = context  # сюда передаём RaSelfMaster и модули

    async def handle_client(self, reader, writer):
        try:
            data = await reader.read(65536)
            message = json.loads(data.decode())
            user_id = message.get("user_id")
            text = message.get("message")

            reply = "⚠️ CORE молчит..."
            if text and self.context:
                if hasattr(self.context, "process_text"):
                    reply = await self.context.process_text(user_id, text)
                else:
                    reply = "⚠️ CORE готов, но process_text не найден."

            response = json.dumps({"response": reply}, ensure_ascii=False)
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            logging.warning(f"[IPC] Ошибка обработки: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        logging.info(f"[IPC] Сервер запущен на {addr}")
        async with server:
            await server.serve_forever()
