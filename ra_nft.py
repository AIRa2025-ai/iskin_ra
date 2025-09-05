import os
import json
import asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
from image_gen import text2im  # твой генератор глифов
from web3.storage import Web3Storage, File  # pip install web3.storage

# --- Настройки ---
PRIVATE_KEY = os.getenv("METAMASK_PRIVATE_KEY")  # Приватный ключ MetaMask
RPC_URL = "https://polygon-rpc.com"  # Сеть Polygon
CONTRACT_ADDRESS = "0xТВОЙ_ERC721_КОНТРАКТ"  # Адрес смарт-контракта
STORAGE_TOKEN = os.getenv("WEB3STORAGE_TOKEN")  # Web3.Storage API ключ

# Подключаемся к сети
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

if not w3.is_connected():
    raise Exception("❌ Не удалось подключиться к сети!")

account = w3.eth.account.from_key(PRIVATE_KEY)
print("✅ Подключено к сети. Аккаунт:", account.address)

# --- Web3.Storage клиент ---
storage = Web3Storage(STORAGE_TOKEN)

async def create_glyph(prompt="Магический глиф Ра"):
    # Генерируем изображение
    images = await text2im(prompt, size="512x512", n=1)
    filename = "glyph.png"
    images[0].save(filename)
    print("✅ Глиф создан:", filename)
    return filename

def upload_to_ipfs(file_path):
    # Загружаем файл на IPFS
    with open(file_path, "rb") as f:
        cid = storage.put([File(f, name=os.path.basename(file_path))])
    url = f"ipfs://{cid}/{os.path.basename(file_path)}"
    print("✅ Загружено на IPFS:", url)
    return url

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

def mint_nft(metadata_uri):
    # Тут пример вызова функции mint на ERC721
    contract_abi = json.load(open("contract_abi.json"))  # ABI контракта
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

    nonce = w3.eth.get_transaction_count(account.address)
    txn = contract.functions.mint(account.address, metadata_uri).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500_000,
        "gasPrice": w3.to_wei("50", "gwei")
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("✅ NFT заминчен! TxHash:", w3.to_hex(tx_hash))
    return tx_hash

# --- Главная функция ---
async def main():
    prompt = "Магический глиф Ра"
    glyph_file = await create_glyph(prompt)
    image_url = upload_to_ipfs(glyph_file)
    metadata_file = create_metadata(
        name="Глиф Ра #1",
        description="Живой магический артефакт",
        image_url=image_url,
        attributes=[{"trait_type": "Сила", "value": 100}]
    )
    metadata_url = upload_to_ipfs(metadata_file)
    mint_nft(metadata_url)

if __name__ == "__main__":
    asyncio.run(main())
