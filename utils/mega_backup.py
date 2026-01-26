# utils/mega_backup.py
import os
from mega import Mega

def upload_memory():
    mega = Mega().login("email", "password")
    m = mega.find("ra_memory_backup")
    if not m:
        m = mega.create_folder("ra_memory_backup")
    mega.upload("memory", m)
