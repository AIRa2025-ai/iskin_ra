# mastodon_client.py
import os, logging
from mastodon import Mastodon, MastodonError

def get_client():
    base_url = os.getenv("MASTODON_BASE_URL")
    token = os.getenv("MASTODON_ACCESS_TOKEN")
    if not base_url or not token:
        logging.warning("⚠️ MASTODON_* переменные не заданы")
        return None
    try:
        return Mastodon(api_base_url=base_url, access_token=token)
    except Exception as e:
        logging.error(f"❌ Mastodon client init: {e}")
        return None

def post_status(text: str) -> bool:
    client = get_client()
    if not client:
        return False
    try:
        client.toot(text[:480])  # лимит поста
        logging.info("🕊️ Mastodon: пост отправлен")
        return True
    except MastodonError as e:
        logging.error(f"❌ Mastodon post: {e}")
        return False
