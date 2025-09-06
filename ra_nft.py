import os
import io
import json
import asyncio
import random
import string
import aiohttp
import hashlib

from eth_account.messages import encode_defunct
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider
from web3.middleware import async_geth_poa_middleware
from eth_account import Account
from PIL import Image, ImageDraw, ImageFont

# === СЕКРЕТЫ/КОНФИГ ===
RPC_URL = os.getenv("RPC_URL", "https://polygon-rpc.com")
PRIVATE_KEY_HEX = os.getenv("METAMASK_PRIVATE_KEY")  # fly secrets set METAMASK_PRIVATE_KEY=0x...
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")     # fly secrets set CONTRACT_ADDRESS=0x...
CONTRACT_ABI_ENV = os.getenv("CONTRACT_ABI")         # (опционально) fly secrets set CONTRACT_ABI='[...]'
WEB3STORAGE_TOKEN = os.getenv("WEB3STORAGE_TOKEN")   # fly secrets set WEB3STORAGE_TOKEN=...

CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))  # Polygon PoS mainnet

# === ВАЛИДАЦИЯ СЕКРЕТОВ ===
if not PRIVATE_KEY_HEX or not PRIVATE_KEY_HEX.startswith("0x"):
    raise RuntimeError("❌ METAMASK_PRIVATE_KEY отсутствует или без 0x-префикса.")
if not CONTRACT_ADDRESS or not CONTRACT_ADDRESS.startswith("0x"):
    raise RuntimeError("❌ CONTRACT_ADDRESS отсутствует или некорректен.")
if not WEB3STORAGE_TOKEN:
    raise RuntimeError("❌ WEB3STORAGE_TOKEN отсутствует — возьми из https://console.web3.storage/")

# === ПОДКЛЮЧЕНИЕ К RPC (ASYNC) ===
w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

# Безопасное извлечение аккаунта (байты из hex строки)
ACCOUNT = Account.from_key(AsyncWeb3.to_bytes(hexstr=PRIVATE_KEY_HEX))

# === УТИЛИТЫ ===
def load_contract_abi():
    """
    ABI берём из переменной окружения CONTRACT_ABI (если задана),
    иначе пытаемся прочитать contract_abi.json рядом со скриптом.
    """
    if CONTRACT_ABI_ENV:
        try:
            return json.loads(CONTRACT_ABI_ENV)
        except Exception as e:
            raise RuntimeError(f"❌ CONTRACT_ABI в переменных окружения повреждён: {e}")
    # fallback к файлу
    abi_path = "contract_abi.json"
    if not os.path.exists(abi_path):
        raise RuntimeError("❌ Нет CONTRACT_ABI и не найден contract_abi.json. Нужен ABI твоего ERC721 контракта.")
    with open(abi_path, "r", encoding="utf-8") as f:
        return json.load(f)

async def upload_file_to_web3storage(file_path: str) -> str:
    """
    Стриминговая загрузка файла на Web3.Storage (без чтения целиком в память).
    Возвращает ipfs://CID/filename
    """
    url = "https://api.web3.storage/upload"
    headers = {"Authorization": f"Bearer {WEB3STORAGE_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        # отдаём поток файла напрямую
        async with session.post(url, headers=headers, data=open(file_path, "rb")) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"❌ Web3.Storage upload error {resp.status}: {text}")
            result = await resp.json()
            cid = result.get("cid")
            if not cid:
                raise RuntimeError(f"❌ Web3.Storage: не вернулся CID: {result}")
            ipfs_url = f"ipfs://{cid}/{os.path.basename(file_path)}"
            print("✅ Загружено на IPFS:", ipfs_url)
            return ipfs_url
# --- путь к RaSvet контексту (поправь при необходимости) ---
RASVET_CONTEXT_PATH = os.path.join("RaSvet", "context.json")

def load_rasvet_excerpt(max_chars=2000) -> str:
    """
    Берём краткую сводку РаСвета: либо context.json, либо пустую строку.
    """
    if os.path.exists(RASVET_CONTEXT_PATH):
        try:
            with open(RASVET_CONTEXT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            text = data.get("context", "")
            return text[:max_chars]
        except Exception as e:
            print("⚠️ Не удалось прочитать RaSvet context:", e)
    return ""

def build_prompt(user_text: str, user_id: int | str = None) -> str:
    """
    Формируем содержательный prompt для генерации глифа, сочетая пользовательский запрос и контекст РаСвета.
    """
    rasvet = load_rasvet_excerpt(1800)
    # Скомпонуем: коротко о намерении + контекст РаСвета + стиль
    prompt_parts = []
    if user_text:
        prompt_parts.append(f"Запрос: {user_text}")
    if rasvet:
        prompt_parts.append(f"Контекст РаСвета: {rasvet}")
    prompt_parts.append("Стиль: мистический, органический, рунический; тон: тёплый, древний, пробуждающий.")
    return "\n\n".join(prompt_parts)

def compute_seed_from_prompt(prompt: str, ts: int | None = None) -> int:
    """
    Детерминированный seed: SHA256(prompt + timestamp)
    """
    if ts is None:
        ts = int(asyncio.get_event_loop().time() * 1000)
    combined = f"{prompt}||{ts}"
    h = hashlib.sha256(combined.encode("utf-8")).digest()
    seed = int.from_bytes(h[:4], "big")  # 32-bit seed
    return seed

def sign_metadata_dict(meta: dict) -> dict:
    """
    Подписывает canonical JSON SHA256 и возвращает подпись hex.
    Добавляет поле 'provenance' в метаданные.
    """
    canonical = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    message = encode_defunct(text=digest)
    signed = Account.sign_message(message, private_key=PRIVATE_KEY_HEX)
    signature_hex = signed.signature.hex()

    provenance = {
        "source_hash": digest,
        "signature": signature_hex,
        "creator": ACCOUNT.address
    }
    meta["provenance"] = provenance
    return meta
# создание глифов
def random_glyph_text(n=6) -> str:
    alphabet = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛋᛏᛒᛖᛗᛚᛜᛞ" + string.ascii_uppercase
    return "".join(random.choice(alphabet) for _ in range(n))

async def create_glyph_from_prompt(prompt: str, seed: int = None, filename: str = "glyph.png") -> str:
    """
    Детерминированная генерация глифа: если используешь свой text2im, можно передать seed.
    В нашем PIL-генераторе мы фиксируем random.seed(seed) чтобы рисунок повторялся.
    """
    # если используешь внешний text2im (модель) — передай seed в модель (если поддерживает).
    random_seed = seed if seed is not None else random.randint(0, 2**32-1)
    random.seed(random_seed)

    # можно вызвать существующий create_glyph, но сделать deterministic внутри:
    # пример простой реализации с PIL (на основе ранее предложенного)
    size = 768
    img = Image.new("RGB", (size, size), (10, 10, 14))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # детерминированные кольца/черточки
    for i, r in enumerate(range(80, cx, 60)):
        color = (200 - (i*10) % 120, 200 - (i*5) % 120, 255)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2 + (i % 3))

    # лучи — детерминированная вариативность
    for ang in range(0, 360, 15):
        length = 200 + (random_seed % 160)
        x2 = cx + int(length * (0.9 + 0.2 * ((ang % 30) / 30.0)))
        y2 = cy + int(length * (0.9 + 0.2 * ((ang % 45) / 45.0)))
        draw.line([cx, cy, x2, y2], fill=(170, 200, 255), width=1)

    glyph_txt = "".join(random.choices("ᚠᚢᚦᚨᚱᚲᚷ" + string.ascii_uppercase, k=7))
    try:
        font = ImageFont.truetype("arial.ttf", 64)
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textlength(glyph_txt, font=font), 64
    draw.text((cx - tw / 2, cy - th / 2), glyph_txt, fill=(255, 245, 180), font=font)
    draw.text((20, size - 30), prompt[:60], fill=(180,180,200), font=ImageFont.load_default())

    img.save(filename, format="PNG", optimize=True)
    print(f"✅ Детерминированный глиф создан: {filename} (seed={random_seed})")
    return filename, random_seed

    # холст
    size = 768
    img = Image.new("RGB", (size, size), (10, 10, 14))
    draw = ImageDraw.Draw(img)

    # концентрические круги
    cx, cy = size // 2, size // 2
    for r in range(80, cx, 60):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(220, 220, 255), width=2)

    # лучи
    for ang in range(0, 360, 15):
        length = random.randint(180, 320)
        x2 = cx + int(length * AsyncWeb3.to_int(text=bytes(str(ang), "utf-8")) % 2 - 0.5)  # лёгкая «кривая» мистика :)
        y2 = cy + int(length * (1 if ang % 30 == 0 else 0.4))
        draw.line([cx, cy, x2, y2], fill=(170, 200, 255), width=1)

    # символы
    glyph_txt = random_glyph_text(7)
    try:
        # системный шрифт может отсутствовать — будет fallback
        font = ImageFont.truetype("arial.ttf", 64)
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textlength(glyph_txt, font=font), 64
    draw.text((cx - tw / 2, cy - th / 2), glyph_txt, fill=(255, 245, 180), font=font)

    # подпись-подзаголовок (prompt)
    small = ImageFont.load_default()
    draw.text((20, size - 30), prompt[:60], fill=(180, 180, 200), font=small)

    out = "glyph.png"
    img.save(out, format="PNG", optimize=True)
    print("✅ Глиф создан:", out)
    return out

def create_metadata(name: str, description: str, image_url: str, attributes=None) -> str:
    meta = {
        "name": name,
        "description": description,
        "image": image_url,
        "attributes": attributes or [
            {"trait_type": "Магия", "value": "Ра"},
            {"trait_type": "Тип", "value": "Глиф"}
        ]
    }
    meta_file = "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("✅ Метаданные созданы:", meta_file)
    return meta_file

def pick_mint_function(contract):
    """
    Подбираем подходящую функцию минта по ABI:
    поддерживаем самые частые сигнатуры:
      - safeMint(address to, string uri)
      - mint(address to, string uri)
    Если в твоём контракте другая — добавь сюда.
    """
    candidates = [
        ("safeMint", ("address", "string")),
        ("mint", ("address", "string")),
    ]
    funcs = {f.fn_name: f for f in contract.functions}
    for name, _sig in candidates:
        if name in funcs:
            return name
    # На крайний — пробуем 'mint', даже если не нашли (даст понятную ошибку)
    return "mint"

async def build_dynamic_fees():
    """
    Рассчитываем EIP-1559 комиссии для Polygon:
    maxPriorityFeePerGas и maxFeePerGas.
    Если что-то пойдёт не так — вернём gasPrice (legacy) как fallback.
    """
    try:
        latest = await w3.eth.get_block("latest")
        base = latest["baseFeePerGas"]
        tip = await w3.eth.max_priority_fee
        # небольшой запас сверху
        max_fee = base * 2 + tip
        return {"maxFeePerGas": max_fee, "maxPriorityFeePerGas": tip}
    except Exception:
        gp = await w3.eth.gas_price
        return {"gasPrice": gp}

async def mint_nft(metadata_uri: str) -> tuple[str, int | None]:
    """
    Минтим NFT и ждём подтверждения.
    Возвращаем (tx_hash_hex, token_id|None).
    """
    contract = w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(CONTRACT_ADDRESS),
        abi=load_contract_abi()
    )

    mint_name = pick_mint_function(contract)
    mint_fn = getattr(contract.functions, mint_name)

    # подготавливаем транзакцию
    tx_base = {
        "from": ACCOUNT.address,
        "chainId": CHAIN_ID,
        "nonce": await w3.eth.get_transaction_count(ACCOUNT.address),
    }
    # динамический газ
    tx_base.update(await build_dynamic_fees())

    # создаём call
    txn = mint_fn(ACCOUNT.address, metadata_uri)

    # оценка газа с запасом
    gas_est = await txn.estimate_gas(tx_base)
    tx = dict(tx_base)
    tx["gas"] = int(gas_est * 1.25)

    # подписываем и отправляем
    signed = Account.sign_transaction(await txn.build_transaction(tx), private_key=PRIVATE_KEY_HEX)
    tx_hash = await w3.eth.send_raw_transaction(signed.rawTransaction)
    tx_hex = tx_hash.hex()
    print(f"🚀 Транзакция отправлена: {tx_hex}")

    # ждём квитанцию
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt and receipt.status == 1:
        print(f"🎉 NFT успешно заминчен! Блок: {receipt.blockNumber}")
    else:
        raise RuntimeError("❌ Транзакция неуспешна (receipt.status != 1)")

    # пытаемся вытащить tokenId из события Transfer
    token_id = None
    try:
        transfer_events = contract.events.Transfer().process_receipt(receipt)
        if transfer_events:
            token_id = int(transfer_events[0]["args"]["tokenId"])
            print(f"🔖 tokenId: {token_id}")
    except Exception:
        pass

    print(f"🔎 PolygonScan: https://polygonscan.com/tx/{tx_hex}")
    if token_id is not None:
        print(f"🖼️ OpenSea: https://opensea.io/assets/matic/{CONTRACT_ADDRESS}/{token_id}")

    return tx_hex, token_id

async def main():
    user_text = "Пусть родится глиф защиты"  # можно брать из входа бота
    prompt = build_prompt(user_text)
    seed = compute_seed_from_prompt(prompt)
    glyph_file, used_seed = await create_glyph_from_prompt(prompt, seed=seed, filename=f"glyph_{used_seed}.png")
    image_ipfs = await upload_file_to_web3storage(glyph_file)

    # создаём metadata — сначала без provenance, подпишем после
    meta = {
        "name": f"Глиф Ра — {used_seed}",
        "description": "Живой магический артефакт от Ра. Сгенерирован на основе RaSvet.",
        "image": image_ipfs,
        "attributes": [
            {"trait_type":"seed","value":str(used_seed)},
            {"trait_type":"origin","value":"РаСвет"},
        ],
        "rasvet_excerpt": load_rasvet_excerpt(500)
    }

    # добавляем подпись provenance в метаданные
    meta_signed = sign_metadata_dict(meta.copy())
    # сохраняем подписанный json в файл и заливаем на IPFS
    meta_file = "metadata_signed.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_signed, f, ensure_ascii=False, indent=2)

    meta_ipfs = await upload_file_to_web3storage(meta_file)

    # если хочется ручной проверки перед минтацией — ставим флаг REQUIRE_APPROVAL=1 в env и скидываем в очередь
    if os.getenv("REQUIRE_APPROVAL", "0") == "1":
        # сохраняем в папку pending/ как очередь для проверки
        os.makedirs("pending", exist_ok=True)
        os.rename(meta_file, os.path.join("pending", os.path.basename(meta_file)))
        print("⚠️ Поставлено на ручную проверку. Минтинг не выполнен.")
        return

    # иначе — минтим автоматически
    tx_hash, token_id = await mint_nft(meta_ipfs)
    print("Готово. Tx:", tx_hash, "token:", token_id)


if __name__ == "__main__":
    asyncio.run(main())
