# core/ra_ipc.py
import asyncio
import json
import logging

class RaIPCServer:
    """
    Локальный IPC-сервер (TCP), для общения CORE и Telegram
    """
    def __init__(self, host="127.0.0.1", port=8765, context=None):
        self.host = host
        self.port = port
        self.context = context  # RaSelfMaster
        self.server = None

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        try:
            data = await reader.read(4096)
            message = data.decode()
            logging.info(f"[IPC] Получено сообщение: {message} от {addr}")

            # Преобразуем JSON
            try:
                payload = json.loads(message)
                user_id = payload.get("user_id")
                text = payload.get("text")
            except Exception:
                payload = {}
                user_id = None
                text = str(message)

            # CORE обрабатывает текст через RaSelfMaster
            reply = "⚠️ CORE пока не ответил"
            if self.context and hasattr(self.context, "process_text"):
                try:
                    reply = await self.context.process_text(user_id, text)
                except Exception as e:
                    logging.warning(f"[IPC] Ошибка process_text: {e}")

            response = json.dumps({"reply": reply})
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            logging.error(f"[IPC] Ошибка handle_client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        addr = self.server.sockets[0].getsockname()
        logging.info(f"[IPC] Сервер запущен на {addr}")
        async with self.server:
            await self.server.serve_forever()
