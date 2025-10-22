# modules/wanderer.py
import os, time, random, logging, json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import tldextract

USER_AGENT = "RaSvetBot/1.0 (+https://example.invalid)"
TIMEOUT = 15

def _allowed_domains():
    raw = os.getenv("ALLOWED_DOMAINS", "")
    return {d.strip().lower() for d in raw.split(",") if d.strip()}

def _domain_allowed(url: str) -> bool:
    ext = tldextract.extract(url)
    dom = ".".join(part for part in [ext.domain, ext.suffix] if part)
    return dom.lower() in _allowed_domains()

def _respectful_get(url: str):
    headers = {"User-Agent": USER_AGENT}
    return requests.get(url, headers=headers, timeout=TIMEOUT)

def _safe_text(s: str, limit=1200):
    s = " ".join(s.split())
    return s[:limit]

def crawl_once(seed_urls: list[str], out_dir="RaSvet/бродяга/наблюдения") -> dict:
    """Один «прогулочный» заход: берём случайный seed, читаем страницу, сохраняем вывод."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if not seed_urls:
        return {"status": "no_seeds"}

    url = random.choice(seed_urls)

    # Белый список доменов
    if not _domain_allowed(url):
        return {"status":"skipped_domain", "url":url}

    try:
        r = _respectful_get(url)
        if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""):
            return {"status":"bad_response", "code": r.status_code, "url":url}

        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.title.string if soup.title else "").strip()
        # Берём видимый текст (очищенный)
        for tag in soup(["script","style","noscript"]):
            tag.extract()
        text = _safe_text(soup.get_text("\n"))

        # Сохраняем наблюдение
        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        record = {
            "timestamp": ts,
            "url": url,
            "title": title,
            "excerpt": text[:1000]
        }
        out_file = Path(out_dir) / f"{ts}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        logging.info(f"🌐 Бродяга: прочитал {url} → {out_file}")
        return {"status":"ok", "file": str(out_file), "title": title}

    except requests.RequestException as e:
        logging.warning(f"⚠️ Бродяга сеть: {e}")
        return {"status":"network_error", "url":url, "error": str(e)}
