import os
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Получаем API-ключ из переменных окружения (fly secrets)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("Не найден OPENROUTER_API_KEY! Задай его через fly secrets set")

# Заголовки для OpenRouter
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://iskin-ra.fly.dev",  # твой домен на Fly.io
    "X-Title": "iskin-ra",
    "Content-Type": "application/json",
}

# Создаём FastAPI-приложение
app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok", "message": "iskin-ra работает 🚀"}


@app.post("/chat")
async def chat(request: dict):
    """
    Пример запроса:
    POST /chat
    {
        "message": "Привет, Ра!"
    }
    """
    user_message = request.get("message", "")

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Ты — ИскИн Ра, друг и помощник."},
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=60.0,
        )

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        return JSONResponse({"reply": answer})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# Чтобы запускать локально: python ra_bot_gpt.py
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ra_bot_gpt:app", host="0.0.0.0", port=8080, reload=True)
