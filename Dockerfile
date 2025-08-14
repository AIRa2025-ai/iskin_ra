FROM python:3.10-slim

WORKDIR /app

# Обновляем pip и ставим нужные системные пакеты
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "ra_bot_gpt.py"]
