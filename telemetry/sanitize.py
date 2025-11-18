# telemetry/sanitize.py
import re
import getpass
import socket
from pathlib import Path

def sanitize_text(text: str) -> str:
    username = getpass.getuser()
    hostname = socket.gethostname()
    home = str(Path.home())

    text = text.replace(home, "<HOME>")
    text = text.replace(username, "<USER>")
    text = text.replace(hostname, "<HOST>")

    text = re.sub(r"C:\\Users\\[^\\]+", r"C:\\Users\\<USER>", text)
    text = re.sub(r"/home/[^/]+", "/home/<USER>", text)
    text = re.sub(r"/Users/[^/]+", "/Users/<USER>", text)

    return text
