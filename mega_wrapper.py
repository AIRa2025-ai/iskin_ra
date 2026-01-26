# mega_wrapper.py
import asyncio
from async_mega_py import Mega

async def upload_file(email, password, local_path):
    m = Mega()
    await m.login(email, password)
    file = await m.upload(local_path)
    return file

def upload_file_sync(email, password, local_path):
    return asyncio.run(upload_file(email, password, local_path))
