# mega_wrapper.py
from mega import Mega  # обычный синхронный Mega-клиент

def upload_file_sync(email, password, local_path):
    try:
        m = Mega()
        m.login(email, password)
        uploaded_file = m.upload(local_path)
        return uploaded_file
    except Exception as e:
        print(f"❌ Ошибка загрузки файла {local_path} в Mega: {e}")
        return None
