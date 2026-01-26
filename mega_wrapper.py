# mega_wrapper.py
from mega.mega import Mega  # синхронный Mega-клиент

def upload_file_sync(email, password, local_path):
    m = Mega()
    m.login(email, password)
    file = m.upload(local_path)
    return file
