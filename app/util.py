import os
import sys
import requests
import time
import shutil
import re

# ===== UI UTILITIES =====
def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

def box_line(text="", color="\033[97m"):
    gray, reset = "\033[90m", "\033[0m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    inner_width = term_width - 4
    pad = inner_width - visible_len(text)
    if pad < 0:
        pad = 0
    return f"{gray}│{reset} {color}{text}{reset}{' ' * pad}{gray}│{reset}"

def box(title="", content_lines=None, color="\033[97m", center=False):
    gray, reset = "\033[90m", "\033[0m"
    cyan = "\033[96m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
    bottom = f"{gray}└{'─' * (term_width - 2)}┘{reset}"

    body = []
    if title:
        if center:
            clean_len = visible_len(title)
            pad_total = term_width - 2 - clean_len
            pad_left = pad_total // 2
            pad_right = pad_total - pad_left
            body.append(f"{gray}│{reset}{' ' * pad_left}{cyan}{title}{reset}{' ' * pad_right}{gray}│{reset}")
        else:
            body.append(box_line(title, cyan))

    if content_lines:
        for c in content_lines:
            body.append(box_line(c, color))

    return "\n".join([top] + body + [bottom])

def spinner(text="Memuat..."):
    anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(15):
        sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
        sys.stdout.flush()
        time.sleep(0.07)
    sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

# ===== ORIGINAL CODE (TIDAK DIUBAH SEDIKITPUN) =====
def load_api_key() -> str:
    if os.path.exists("api.key"):
        with open("api.key", "r", encoding="utf8") as f:
            api_key = f.read().strip()
        if api_key:
            print(box("API KEY", ["API key loaded successfully."], "\033[92m"))
            return api_key
        else:
            print(box("API KEY", ["API key file is empty."], "\033[93m"))
            return ""
    else:
        print(box("API KEY", ["API key file not found."], "\033[91m"))
        return ""
    
def save_api_key(api_key: str):
    with open("api.key", "w", encoding="utf8") as f:
        f.write(api_key)
    print(box("API KEY", ["API key saved successfully."], "\033[92m"))
    
def delete_api_key():
    if os.path.exists("api.key"):
        os.remove("api.key")
        print(box("API KEY", ["API key file deleted."], "\033[93m"))
    else:
        print(box("API KEY", ["API key file does not exist."], "\033[91m"))

def verify_api_key(api_key: str, *, timeout: float = 10.0) -> bool:
    try:
        url = f"https://crypto.mashu.lol/api/verify?key={api_key}"
        print(box("VERIFYING API KEY", ["Connecting to server..."], "\033[96m"))
        spinner("Verifying API key")
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            json_resp = resp.json()
            info_lines = [
                f"Id: {json_resp.get('user_id')}",
                f"Owner: @{json_resp.get('username')}",
                f"Credit: {json_resp.get('credit')}",
                f"Premium Credit: {json_resp.get('premium_credit')}"
            ]
            print(box("API KEY VALID ✅", info_lines, "\033[92m"))
            return True
        else:
            print(box("API KEY INVALID ❌", [f"Server responded with status code {resp.status_code}"], "\033[91m"))
            return False
    except requests.RequestException as e:
        print(box("NETWORK ERROR ⚠️", [f"Failed to verify API key: {e}"], "\033[91m"))
        return False

def get_user_info(api_key: str, *, timeout: float = 10.0) -> dict:
    try:
        url = f"https://crypto.mashu.lol/api/verify?key={api_key}"
        spinner("Fetching user info")
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            print(box("USER INFO", ["Data retrieved successfully."], "\033[92m"))
            return resp.json()
        else:
            print(box("FAILED", [f"HTTP {resp.status_code} {resp.text}"], "\033[91m"))
            raise Exception(f"Failed to fetch user info: {resp.status_code} {resp.text}")
    except requests.RequestException as e:
        print(box("NETWORK ERROR ⚠️", [f"Error: {e}"], "\033[91m"))
        raise Exception(f"Network error while fetching user info: {e}") from e

def ensure_api_key() -> str:
    current = load_api_key()
    if current:
        if verify_api_key(current):
            return current
        else:
            print(box("INVALID KEY", ["Existing API key is invalid. Please enter a new one."], "\033[93m"))

    print(box("INFO", ["Dapatkan API key di Bot Telegram @fyxt_bot"], "\033[96m"))
    api_key = input("\033[96mMasukkan API key:\033[0m ").strip()
    if not api_key:
        print(box("ERROR", ["API key tidak boleh kosong. Menutup aplikasi."], "\033[91m"))
        sys.exit(1)

    if not verify_api_key(api_key):
        print(box("ERROR", ["API key tidak valid. Menutup aplikasi."], "\033[91m"))
        delete_api_key()
        sys.exit(1)

    save_api_key(api_key)
    return api_key