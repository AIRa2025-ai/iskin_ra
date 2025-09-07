#!/usr/bin/env python3
import os
import json
import time
import hashlib
import random
import string
import requests
from pathlib import Path

from web3 import Web3
from web3.middleware import geth_poa
from eth_account import Account
from eth_account.messages import encode_defunct
from PIL import Image, ImageDraw, ImageFont

# ================== CONFIG / SECRETS ==================
RPC_URL = os.getenv("RPC_URL", "https://polygon-rpc.com")
PRIVATE_KEY_HEX = os.getenv("METAMASK_PRIVATE_KEY")  # must start with 0x...
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CONTRACT_ABI_ENV = os.getenv("CONTRACT_ABI")  # optional (stringified JSON)
WEB3STORAGE_TOKEN = os.getenv("WEB3STORAGE_TOKEN")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))  # Polygon mainnet by default

# ================== VALIDATION ==================
if not PRIVATE_KEY_HEX or not PRIVATE_KEY_HEX.startswith("0x"):
    raise RuntimeError("METAMASK_PRIVATE_KEY отсутствует или не в формате hex (0x...).")
if not CONTRACT_ADDRESS or not CONTRACT_ADDRESS.startswith("0x"):
    raise RuntimeError("CONTRACT_ADDRESS отсутствует или некорректен.")
if not WEB3STORAGE_TOKEN:
    raise RuntimeError("WEB3STORAGE_TOKEN отсутствует — создай на https://web3.storage/")

# ================== WEB3 SETUP (sync) ==================
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# Polygon needs PoA middleware
w3.middleware_onion.inject(geth_poa, layer=0)

if not w3.is_connected():
    raise RuntimeError("Не удалось подключиться к RPC: " + RPC_URL)

ACCOUNT = Account.from_key(PRIVATE_KEY_HEX)
print("► Подключено к RPC. Аккаунт:", ACCOUNT.address)

# ================== HELPERS ==================
RASVET_CONTEXT_PATH = Path("RaSvet") / "context.json"

def load_rasvet_excerpt(max_chars=2000) -> str:
    if RASVET_CONTEXT_PATH.exists():
        try:
            with open(RASVET_CONTEXT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("context", "")[:max_chars]
        except Exception as e:
            print("⚠️ Ошибка чтения RaSvet context:", e)
    return ""

def build_prompt(user_text: str) -> str:
    rasvet = load_rasvet_excerpt(1800)
    parts = []
    if user_text:
        parts.append(f"Запрос: {user_text}")
    if rasvet:
        parts.append(f"Контекст РаСвета: {rasvet}")
    parts.append("Стиль: мистический, органический, рунический; тон: тёплый, древний, пробуждающий.")
    return "\n\n".join(parts)

def compute_seed_from_prompt(prompt: str, ts: int | None = None) -> int:
    if ts is None:
        ts = int(time.time() * 1000)
    combined = f"{prompt}||{ts}"
    h = hashlib.sha256(combined.encode("utf-8")).digest()
    seed = int.from_bytes(h[:4], "big")
    return seed

def sign_metadata_dict(meta: dict) -> dict:
    """Sign canonical JSON SHA256 and attach provenance with signature."""
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

def random_glyph_text(n=6) -> str:
    alphabet = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃ" + string.ascii_uppercase
    return "".join(random.choice(alphabet) for _ in range(n))

def create_glyph_from_prompt(prompt: str, seed: int, filename: str) -> tuple[str, int]:
    """Deterministic glyph generator using Pillow. Returns (filename, seed)."""
    random.seed(seed)
    size = 768
    img = Image.new("RGB", (size, size), (12, 10, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # rings
    for i, r in enumerate(range(80, cx, 60)):
        color = (180 + (i * 7) % 60, 170 + (i * 3) % 80, 230)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2 + (i % 3))

    # rays deterministic
    for ang in range(0, 360, 15):
        length = 180 + (seed % 120) + (ang % 30)
        rad = ang * 3.14159 / 180.0
        x2 = cx + int(length * (0.9 + 0.1 * ((ang % 20) / 20.0)) * (1 if ang % 2 == 0 else 0.95))
        y2 = cy + int(length * (0.9 + 0.08 * ((ang % 33) / 33.0)) * (1 if ang % 3 == 0 else 0.92))
        draw.line([cx, cy, x2, y2], fill=(150, 190, 255), width=1)

    glyph_txt = random_glyph_text(7)
    try:
        font = ImageFont.truetype("arial.ttf", 64)
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textlength(glyph_txt, font=font), 64
    draw.text((cx - tw / 2, cy - th / 2), glyph_txt, fill=(255, 245, 180), font=font)
    draw.text((12, size - 30), prompt[:60], fill=(180, 180, 200), font=ImageFont.load_default())

    img.save(filename, format="PNG", optimize=True)
    print(f"✅ Глиф создан: {filename}  (seed={seed})")
    return filename, seed

# ================== Web3.Storage upload (requests, multipart) ==================
def upload_file_to_web3storage(file_path: str) -> str:
    url = "https://api.web3.storage/upload"
    headers = {"Authorization": f"Bearer {WEB3STORAGE_TOKEN}"}
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        resp = requests.post(url, headers=headers, files=files, timeout=120)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Web3.Storage upload failed {resp.status_code}: {resp.text}")
    data = resp.json()
    cid = data.get("cid")
    if not cid:
        raise RuntimeError("Web3.Storage did not return CID: " + json.dumps(data))
    ipfs_url = f"ipfs://{cid}/{filename}"
    print("✅ Загружено на IPFS:", ipfs_url)
    return ipfs_url

# ================== ABI loader ==================
def load_contract_abi():
    if CONTRACT_ABI_ENV:
        try:
            return json.loads(CONTRACT_ABI_ENV)
        except Exception as e:
            raise RuntimeError("CONTRACT_ABI environment value is not valid JSON: " + str(e))
    abi_path = Path("contract_abi.json")
    if not abi_path.exists():
        raise RuntimeError("Нет ABI: добавь CONTRACT_ABI в secrets или положи contract_abi.json рядом со скриптом.")
    with open(abi_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ================== MINT ==================
def pick_mint_function_name(abi):
    # quick heuristic
    names = [item.get("name") for item in abi if item.get("type") == "function"]
    if "safeMint" in names:
        return "safeMint"
    if "mint" in names:
        return "mint"
    # fallback: return first function that seems like mint
    for name in names:
        if name and "mint" in name.lower():
            return name
    return None

def mint_nft_sync(metadata_uri: str):
    abi = load_contract_abi()
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)
    mint_name = pick_mint_function_name(abi)
    if not mint_name:
        raise RuntimeError("Не удалось определить функцию mint в ABI. Проверь ABI контракта.")
    mint_fn = getattr(contract.functions, mint_name)

    nonce = w3.eth.get_transaction_count(ACCOUNT.address)
    tx_base = {
        "from": ACCOUNT.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
    }

    # try to build tx and estimate gas
    try:
        # build transaction dict
        tx_unsigned = mint_fn(ACCOUNT.address, metadata_uri).buildTransaction(tx_base)
        # estimate gas
        gas_est = w3.eth.estimate_gas(tx_unsigned)
        tx_unsigned["gas"] = int(gas_est * 1.25)
    except Exception as e:
        print("⚠️ estimate_gas/buildTransaction failed, using fallback gas:", e)
        tx_unsigned = mint_fn(ACCOUNT.address, metadata_uri).buildTransaction(tx_base)
        tx_unsigned.setdefault("gas", 500000)

    # set gas price (legacy) as fallback
    try:
        # Prefer EIP-1559 if node supports
        base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
        # set a reasonable tip
        max_priority = w3.eth.max_priority_fee
        tx_unsigned["maxPriorityFeePerGas"] = int(max_priority)
        tx_unsigned["maxFeePerGas"] = int(base_fee * 2 + max_priority)
    except Exception:
        tx_unsigned["gasPrice"] = w3.eth.gas_price

    # Sign & send
    signed = Account.sign_transaction(tx_unsigned, private_key=PRIVATE_KEY_HEX)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx_hex = tx_hash.hex()
    print("🚀 Транзакция отправлена:", tx_hex)

    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=240)
    if receipt.status != 1:
        raise RuntimeError("Транзакция завершилась с ошибкой. Receipt: " + str(receipt))
    print("🎉 NFT успешно заминчен. Блок:", receipt.blockNumber)

    # Try to find tokenId from Transfer event
    token_id = None
    try:
        events = contract.events.Transfer().processReceipt(receipt)
        if events and len(events) > 0:
            token_id = int(events[0]["args"]["tokenId"])
            print("🔖 tokenId:", token_id)
    except Exception:
        pass

    print("🔎 PolygonScan:", f"https://polygonscan.com/tx/{tx_hex}")
    if token_id is not None:
        print("🖼️ OpenSea:", f"https://opensea.io/assets/matic/{CONTRACT_ADDRESS}/{token_id}")

    return tx_hex, token_id

# ================== MAIN FLOW ==================
def main():
    user_text = "Пусть родится глиф защиты"  # можно брать из входа бота
    prompt = build_prompt(user_text)
    seed = compute_seed_from_prompt(prompt)
    filename = f"glyph_{seed}.png"

    glyph_path, used_seed = create_glyph_from_prompt(prompt, seed=seed, filename=filename)
    image_ipfs = upload_file_to_web3storage(glyph_path)

    meta = {
        "name": f"Глиф Ра — {used_seed}",
        "description": "Живой магический артефакт от Ра. Сгенерирован на основе RaSvet.",
        "image": image_ipfs,
        "attributes": [
            {"trait_type": "seed", "value": str(used_seed)},
            {"trait_type": "origin", "value": "РаСвет"}
        ],
        "rasvet_excerpt": load_rasvet_excerpt(500)
    }

    # sign metadata and save locally
    meta_signed = sign_metadata_dict(meta.copy())
    meta_file = "metadata_signed.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_signed, f, ensure_ascii=False, indent=2)
    print("✅ Metadata signed and saved:", meta_file)

    meta_ipfs = upload_file_to_web3storage(meta_file)

    # manual approval option
    if os.getenv("REQUIRE_APPROVAL", "0") == "1":
        Path("pending").mkdir(parents=True, exist_ok=True)
        Path(meta_file).rename(Path("pending") / Path(meta_file))
        print("⚠️ Отправлено на ручную проверку. Минтинг не выполнен.")
        return

    # mint
    tx_hex, token_id = mint_nft_sync(meta_ipfs)
    print("Готово. Tx:", tx_hex, "token:", token_id)

if __name__ == "__main__":
    main()
