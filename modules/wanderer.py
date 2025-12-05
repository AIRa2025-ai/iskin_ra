# modules/wanderer_v2.py
# -*- coding: utf-8 -*-
"""
RaSvet Wanderer 2.0 — продвинутый сборщик наблюдений:
- обход ссылок внутри разрешённых доменов
- сбор метаданных (title, description, keywords)
- сохранение текста и кратких выдержек
- логирование действий
"""

import os, time, random, logging, json
from pathlib import Path
from urllib.parse import urljoin, urlparse  # noqa: F401

import requests
from bs4 import BeautifulSoup
import tldextract

USER_AGENT = "RaSvetBot/2.0 (+https://example.invalid)"
TIMEOUT = 15
MAX_DEPTH = 2  # макс глубина обхода ссылок

# --- Настройка логов ---
LOG_DIR = Path("RaSvet/бродяга/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "wanderer.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

# --- Полезные функции ---
def _allowed_domains():
    """Разрешённые домены через переменные окружения"""
    raw = os.getenv("ALLOWED_DOMAINS", "")
    return {d.strip().lower() for d in raw.split(",") if d.strip()}

def _domain_allowed(url: str) -> bool:
    ext = tldextract.extract(url)
    dom = ".".join(part for part in [ext.domain, ext.suffix] if part)
    return dom.lower() in _allowed_domains()

def _respectful_get(url: str):
    headers = {"User-Agent": USER_AGENT}
    return requests.get(url, headers=headers, timeout=TIMEOUT)

def _safe_text(s: str, limit=5000):
    s = " ".join(s.split())
    return s[:limit]

def _extract_meta(soup):
    """Собираем title, description, keywords"""
    meta = {}
    meta["title"] = soup.title.string.strip() if soup.title else ""
    desc = soup.find("meta", attrs={"name":"description"})
    meta["description"] = desc["content"].strip() if desc and "content" in desc.attrs else ""
    keys = soup.find("meta", attrs={"name":"keywords"})
    meta["keywords"] = keys["content"].strip() if keys and "content" in keys.attrs else ""
    return meta

def _collect_links(soup, base_url):
    """Собираем все ссылки на странице внутри разрешённых доменов"""
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if _domain_allowed(href):
            links.add(href)
    return list(links)

def crawl_page(url: str, out_dir="RaSvet/бродяга/наблюдения") -> dict:
    """Собираем данные с одной страницы"""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    try:
        r = _respectful_get(url)
        if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""):
            return {"status":"bad_response", "code": r.status_code, "url":url}

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript"]):
            tag.extract()

        text_full = _safe_text(soup.get_text("\n"))
        meta = _extract_meta(soup)
        links = _collect_links(soup, url)

        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        record = {
            "timestamp": ts,
            "url": url,
            "meta": meta,
            "excerpt": text_full[:1000],
            "full_text": text_full,
            "links": links
        }
        out_file = Path(out_dir) / f"{ts}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        logging.info(f"🌐 Бродяга2: прочитал {url} → {out_file}")
        return {"status":"ok", "file": str(out_file), "meta": meta, "links": links}

    except requests.RequestException as e:
        logging.warning(f"⚠️ Бродяга сеть: {e}")
        return {"status":"network_error", "url":url, "error": str(e)}

def wander(seed_urls: list[str], out_dir="RaSvet/бродяга/наблюдения", depth=0, max_depth=MAX_DEPTH, visited=None):
    """Обход seed-страниц с переходом по ссылкам"""
    if visited is None:
        visited = set()
    if not seed_urls or depth > max_depth:
        return

    url = random.choice(seed_urls)
    if url in visited:
        return
    visited.add(url)

    result = crawl_page(url, out_dir)
    # Рекурсивно идём по ссылкам на текущей странице
    if result.get("links"):
        for link in result["links"]:
            wander([link], out_dir=out_dir, depth=depth+1, max_depth=max_depth, visited=visited)
    return visited

# --- Пример использования ---
if __name__ == "__main__":
    seeds = ["https://example.com"]  # замените на свои стартовые URL
    visited_pages = wander(seeds)
    print(f"🌟 Посещено страниц: {len(visited_pages)}")
