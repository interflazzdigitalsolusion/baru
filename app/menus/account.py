from app.client.engsel import get_otp, submit_otp
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
import shutil
from itertools import cycle
import re
import time, sys

def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

def center_ansi_text(text, width):
    pad_total = width - visible_len(text)
    pad_left = pad_total // 2 if pad_total > 0 else 0
    return " " * pad_left + text

def color_title(title):
    colors = ["\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[94m", "\033[95m"]
    bold, reset = "\033[1m", "\033[0m"
    color_cycle = cycle(colors)
    return "".join(bold + next(color_cycle) + ch if ch.strip() else ch for ch in title) + reset

def box_line(text="", color="\033[97m", padding=1):
    gray, reset = "\033[90m", "\033[0m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    inner_width = term_width - 4
    visible_length = visible_len(text)
    pad_space = inner_width - visible_length
    if pad_space < 0:
        pad_space = 0
    return f"{gray}│{reset} {' ' * padding}{color}{text}{reset}{' ' * pad_space}{gray}│{reset}"

def box(title="", content_lines=None, color="\033[97m"):
    gray, reset = "\033[90m", "\033[0m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
    bottom = f"{gray}└{'─' * (term_width - 2)}┘{reset}"
    body = []
    if title:
        body.append(box_line(title, "\033[96m"))
    if content_lines:
        for c in content_lines:
            body.append(box_line(c, color))
    return "\n".join([top] + body + [bottom])

def spinner(text="Memproses..."):
    anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(10):
        sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

def show_login_menu():
    clear_screen()
    reset, gray = "\033[0m", "\033[90m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    title = color_title(" LOGIN KE MYXL ")
    clean_len = visible_len(title)
    pad_total = term_width - 2 - clean_len
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    print(gray + "┌" + "─" * (term_width - 2) + "┐" + reset)
    print(gray + "│" + reset + " " * pad_left + title + " " * pad_right + gray + "│" + reset)
    print(gray + "├" + "─" * (term_width - 2) + "┤" + reset)
    print(box_line("1. Request OTP"))
    print(box_line("2. Submit OTP"))
    print(box_line("99. Tutup aplikasi"))
    print(gray + "└" + "─" * (term_width - 2) + "┘" + reset)
    print()

def login_prompt(api_key: str):
    clear_screen()
    reset, gray, bold, white, green, red = (
        "\033[0m", "\033[90m", "\033[1m", "\033[97m", "\033[92m", "\033[91m"
    )
    term_width = shutil.get_terminal_size((80, 20)).columns
    title = color_title(" LOGIN KE MYXL ")
    clean_len = visible_len(title)
    pad_total = term_width - 2 - clean_len
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    print(gray + "┌" + "─" * (term_width - 2) + "┐" + reset)
    print(gray + "│" + reset + " " * pad_left + title + " " * pad_right + gray + "│" + reset)
    print(gray + "└" + "─" * (term_width - 2) + "┘" + reset)
    print(box("Masukan Nomor XL", ["Contoh: 6281234567890"]))
    sys.stdout.write(f"{gray}│{reset} {white}Nomor: {green}")
    sys.stdout.flush()
    phone_number = input().strip()
    print(f"{reset}{gray}└{'─' * (term_width - 2)}┘{reset}")
    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print(box("❌ Nomor tidak valid!", ["Pastikan diawali 628 dan panjang benar."], red))
        pause()
        return None
    try:
        spinner("Mengirim OTP...")
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print(box("⚠️ Gagal Mengirim OTP", ["Silakan coba lagi."], red))
            return None
        print(box("✅ OTP Berhasil Dikirim", ["Silakan cek SMS Anda."], green))
        try_count = 5
        while try_count > 0:
            print(box("Masukkan OTP", [f"Sisa percobaan: {try_count}"]))
            sys.stdout.write(f"{gray}│{reset} {white}OTP (6 digit): {white}")
            sys.stdout.flush()
            otp = input().strip()
            print(f"{reset}{gray}└{'─' * (term_width - 2)}┘{reset}")
            if not otp.isdigit() or len(otp) != 6:
                print(box("❌ OTP tidak valid", ["Harus 6 digit angka."], red))
                continue
            spinner("Memverifikasi OTP...")
            tokens = submit_otp(api_key, phone_number, otp)
            if not tokens:
                try_count -= 1
                print(box("❌ OTP salah", ["Silakan coba lagi."], red))
                continue
            print(box("✅ Berhasil Login!", [f"Nomor: {phone_number}"], green))
            return phone_number, tokens["refresh_token"]
        print(box("❌ Gagal Login", ["Terlalu banyak percobaan."], red))
        return None, None
    except Exception:
        print(box("⚠️ Error", ["Koneksi atau server bermasalah."], red))
        return None, None

def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        reset, gray, bold, white, yellow, cyan, green, red = (
            "\033[0m", "\033[90m", "\033[1m", "\033[97m", "\033[93m", "\033[96m", "\033[92m", "\033[91m"
        )
        term_width = shutil.get_terminal_size((80, 20)).columns
        title = color_title(" AKUN TERSIMPAN ")
        clean_len = visible_len(title)
        pad_total = term_width - 2 - clean_len
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        print(gray + "┌" + "─" * (term_width - 2) + "┐" + reset)
        print(gray + "│" + reset + " " * pad_left + title + " " * pad_right + gray + "│" + reset)
        print(gray + "└" + "─" * (term_width - 2) + "┘" + reset)
        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print(box("❌ Gagal menambah akun", ["Silahkan coba lagi."], red))
                pause()
                continue
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            add_user = False
            continue
        akun_lines = []
        if not users or len(users) == 0:
            akun_lines.append("Tidak ada akun tersimpan.")
        else:
            for idx, user in enumerate(users):
                active = active_user and user["number"] == active_user["number"]
                marker = "(Aktif)" if active else ""
                akun_lines.append(f"{idx + 1}. {cyan}{user['number']}{reset} {green if active else ''}{marker}{reset}")
        print(box("Daftar Akun", akun_lines))
        print(box("Command", [
            "0: Tambah Akun",
            "del <nomor>: Hapus akun",
            "00: Kembali ke menu utama"
        ], yellow))
        sys.stdout.write(f"{gray}│{reset} {cyan}Pilihan: {cyan}")
        sys.stdout.flush()
        input_str = input().strip()
        print(f"{reset}{gray}└{'─' * (term_width - 2)}┘{reset}")
        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user["number"]
        elif input_str.startswith("del "):
            parts = input_str.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_index = int(parts[1])
                if active_user and users[del_index - 1]["number"] == active_user["number"]:
                    print(box("⚠️ Tidak dapat hapus akun aktif", ["Ganti akun terlebih dahulu."], yellow))
                    pause()
                    continue
                if 1 <= del_index <= len(users):
                    user_to_delete = users[del_index - 1]
                    confirm = input(f"Yakin hapus akun {user_to_delete['number']}? (y/n): ")
                    if confirm.lower() == 'y':
                        AuthInstance.remove_refresh_token(user_to_delete["number"])
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print(box("✅ Akun dihapus", [user_to_delete["number"]], green))
                        pause()
                    else:
                        print(box("ℹ️ Dibatalkan", [], yellow))
                        pause()
                else:
                    print(box("❌ Nomor urut tidak valid", [], red))
                    pause()
            else:
                print(box("❌ Format salah", ["Gunakan: del <nomor urut>"], red))
                pause()
        else:
            print(box("❌ Input tidak valid", ["Silakan coba lagi."], red))
            pause()