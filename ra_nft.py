import os
import json
import asyncio
import aiohttp
from web3 import Web3
from web3.middleware import geth_poa_middleware
from image_gen import text2im  # твой генератор глифов

# --- Настройки из секретов Fly ---
PRIVATE_KEY = os.getenv("METAMASK_PRIVATE_KEY")
STORAGE_TOKEN = os.getenv("WEB3STORAGE_TOKEN")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = "https://polygon-rpc.com"

# --- Подключение к сети ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

if not w3.is_connected():
    raise Exception("❌ Не удалось подключиться к сети!")

account = w3.eth.account.from_key(PRIVATE_KEY)
print("✅ Подключено к сети. Аккаунт:", account.address)

# --- Функции для Web3.Storage через REST API ---
async def upload_file_to_web3storage(file_path):
    url = "https://api.web3.storage/upload"
    headers = {"Authorization": f"Bearer {STORAGE_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        with open(file_path, "rb") as f:
            data = f.read()
        async with session.post(url, headers=headers, data=data) as resp:
            result = await resp.json()
            cid = result["cid"]
            ipfs_url = f"ipfs://{cid}/{os.path.basename(file_path)}"
            print("✅ Загружено на IPFS:", ipfs_url)
            return ipfs_url

# --- Генерация глифа ---
async def create_glyph(prompt="Магический глиф Ра"):
    images = await text2im(prompt, size="512x512", n=1)
    filename = "glyph.png"
    images[0].save(filename)
    print("✅ Глиф создан:", filename)
    return filename

# --- Создание metadata ---
def create_metadata(name, description, image_url, attributes=None):
    meta = {
        "name": name,
        "description": description,
        "image": image_url,
        "attributes": attributes or []
    }
    meta_file = "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("✅ Метаданные созданы:", meta_file)
    return meta_file

# --- Минт NFT ---
def mint_nft(metadata_uri):
    contract_abi = json.load(open("contract_abi.json"))
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

    nonce = w3.eth.get_transaction_count(account.address)
    txn = contract.functions.mint(account.address, metadata_uri).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500_000,
        "gasPrice": w3.to_wei("50", "gwei")
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw
