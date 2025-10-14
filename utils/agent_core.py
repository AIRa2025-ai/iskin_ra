import os
import asyncio
import logging
import datetime
from gpt_module import safe_ask_openrouter as ask_openrouter
from self_reflection import self_reflect_and_update
from github_commit import create_commit_push

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

class AgentCore:
    def __init__(self):
        self.user_id = "core_agent"
        self.memory_path = "memory/"
        os.makedirs(self.memory_path, exist_ok=True)

    async def ask(self, message):
        """Обращение к OpenRouter с fallback"""
        messages = [{"role": "user", "content": message}]
        logging.info(f"💬 Отправка запроса GPT: {message[:50]}...")
        try:
            answer = await ask_openrouter(self.user_id, messages)
            logging.info(f"💡 Ответ GPT получен: {answer[:50]}...")
            return answer
        except Exception as e:
            logging.error(f"❌ Ошибка при запросе GPT: {e}")
            return f"Ошибка GPT: {e}"

    async def self_update(self):
        """Запуск процесса самоанализа и улучшения кода"""
        logging.info("🧠 Запуск self-reflection...")
        await self_reflect_and_update()

    def create_pr_for_files(self, files_dict, msg="Auto-update by Ra"):
        """Коммит и PR на GitHub"""
        branch_name = f"auto-update-{os.getpid()}"
        pr = create_commit_push(branch_name, files_dict, msg)
        logging.info(f"✅ PR создан: {pr['html_url']}")
        return pr

    async def run(self):
        logging.info("🚀 AgentCore стартует...")
        # Пример: обычный диалог
        answer = await self.ask("Привет, Ра! Как сам?")
        logging.info(f"Ответ GPT: {answer}")

        # Самообновление кода
        await self.self_update()
        logging.info("✨ AgentCore завершил цикл.")

if __name__ == "__main__":
    core = AgentCore()
    asyncio.run(core.run())
