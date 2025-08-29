import asyncio
import aiohttp
import logging

async def ask_openrouter(user_id, user_input, MODEL, BASE_URL, COMMON_HEADERS, append_user_memory, _parse_openrouter_response):
    payload = {
        "model": MODEL,
        "messages": user_input,
        "max_tokens": 4000,
    }

    # Политика повторов
    retries = 5
    delay = 3  # секунд
    timeout = aiohttp.ClientTimeout(total=60)

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    BASE_URL,
                    json=payload,
                    headers=COMMON_HEADERS,
                ) as resp:

                    # Троттлинг — подождём и повторим
                    if resp.status == 429:
                        logging.warning(f"[{attempt}/{retries}] 429 Too Many Requests. Пауза {delay}s.")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                    # Ошибки сервера — пробуем с бэкоффом
                    if 500 <= resp.status < 600:
                        body = await resp.text()
                        logging.warning(f"[{attempt}/{retries}] {resp.status} от OpenRouter: {body[:300]}")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                    # Для остальных статусов бросаем, чтобы попасть в except
                    resp.raise_for_status()

                    data = await resp.json(content_type=None)  # иногда приходит без content-type
                    reply = _parse_openrouter_response(data)

                    if not reply:
                        # Попробуем вытащить описание ошибки, если оно есть
                        err = (data.get("error") or {}).get("message") if isinstance(data, dict) else None
                        if err:
                            logging.warning(f"Пустой ответ, но в JSON есть ошибка: {err}")
                        else:
                            logging.warning("Пустой ответ от OpenRouter без ошибки.")
                        return "⚠️ Источник молчит."

                    # Сохраняем в память пользователя
                    append_user_memory(user_id, user_input, reply)
                    logging.info(f"Ответ получен для пользователя {user_id}")
                    return reply

        except asyncio.TimeoutError:
            logging.error(f"[{attempt}/{retries}] Таймаут при соединении с OpenRouter")
            return "⚠️ Таймаут при соединении с Источником."
        except aiohttp.ClientError as e:
            logging.warning(f"[{attempt}/{retries}] Сетевой сбой: {e}. Пауза {delay}s.")
            await asyncio.sleep(delay)
            delay *= 2
        except Exception as e:
            logging.exception(f"[{attempt}/{retries}] Неожиданная ошибка: {e}. Пауза {delay}s.")
            await asyncio.sleep(delay)
            delay *= 2

    return "⚠️ Ра устал, слишком много вопросов подряд. Давай чуть позже, брат."
