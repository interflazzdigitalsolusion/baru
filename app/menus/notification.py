from app.menus.util import clear_screen, pause
from app.client.engsel import get_notifications, get_notification_detail
from app.service.auth import AuthInstance
import shutil, sys, re, time, textwrap
from itertools import cycle

WIDTH = 55

def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

def box_line(text="", color="\033[97m"):
    gray, reset = "\033[90m", "\033[0m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    inner_width = term_width - 4
    visible_length = visible_len(text)
    pad_space = inner_width - visible_length - 1
    if pad_space < 0:
        pad_space = 0
    return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 2)}{gray}│{reset}"

def center_title(title, color="\033[96m"):
    gray, reset = "\033[90m", "\033[0m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    clean_len = visible_len(title)
    pad_total = term_width - 2 - clean_len
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    return f"{gray}│{reset}{' ' * pad_left}{color}{title}{reset}{' ' * pad_right}{gray}│{reset}"

def box(title="", content_lines=None, color="\033[97m", center=False):
    gray, reset = "\033[90m", "\033[0m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
    bottom = f"{gray}└{'─' * (term_width - 2)}┘{reset}"
    body = []
    if title:
        if center:
            body.append(center_title(title))
        else:
            body.append(box_line(title, "\033[96m"))
    if content_lines:
        for c in content_lines:
            body.append(box_line(c, color))
    return "\n".join([top] + body + [bottom])

def spinner(text="Memuat..."):
    anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(10):
        sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

def input_box(prompt):
    gray, reset, cyan = "\033[90m", "\033[0m", "\033[96m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    text = f"{cyan}{prompt}{reset}"
    inner_width = term_width - 6
    pad = inner_width - visible_len(prompt) - 4

    # Border atas tetap, hilangkan bawah & kanan, input sejajar di kanan label
    sys.stdout.write(f"{gray}┌{'─' * (term_width - 2)}┐{reset}\n")
    sys.stdout.write(f"{gray}│{reset} {text}{cyan} {reset}")
    sys.stdout.flush()

def wrap_text(text, width):
    wrapped = textwrap.wrap(text, width=width)
    return wrapped if wrapped else [""]

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        print(box("Memuat notifikasi...", [], center=True))
        spinner("Fetching notifications")
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        notifications_res = get_notifications(api_key, tokens)
        if not notifications_res:
            print(box("⚠️ Tidak ada notifikasi ditemukan.", [], center=True))
            pause()
            return
        notifications = notifications_res.get("data", {}).get("inbox", [])
        if not notifications:
            print(box("ℹ️ Tidak ada notifikasi tersedia.", [], center=True))
            pause()
            return
        gray, reset, cyan, green, yellow = "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m"
        print(box("NOTIFICATIONS", [], center=True))
        term_width = shutil.get_terminal_size((80, 20)).columns
        wrap_width = term_width - 8
        unread_count = 0
        for idx, notification in enumerate(notifications):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "")
            brief_message = notification.get("brief_message", "")
            time_ = notification.get("timestamp", "")
            status = f"{green}READ{reset}" if is_read else f"{yellow}UNREAD{reset}"
            if not is_read:
                unread_count += 1
            lines = [
                f"{cyan}{idx+1}.{reset} [{status}] {brief_message}",
                f"{gray}Time:{reset} {time_}",
                f"{gray}Msg:{reset}"
            ]
            msg_lines = wrap_text(full_message, wrap_width)
            for line in msg_lines:
                lines.append(f"  {line}")
            print(box("", lines))
        footer = [
            f"{cyan}Total:{reset} {len(notifications)}    {yellow}Unread:{reset} {unread_count}",
            "",
            f"{cyan}1.{reset} Tandai semua belum dibaca → Baca",
            f"{cyan}00.{reset} Kembali ke menu utama"
        ]
        print(box("", footer))
        input_box("Masukkan pilihan:")
        choice = input().strip()
        if choice == "1":
            clear_screen()
            print(box("Menandai semua notifikasi belum dibaca...", [], center=True))
            spinner("Processing")
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    print(box(f"✅ Ditandai READ → ID {notification_id}", [], center=True))
            input_box("Tekan Enter untuk kembali...")
            input()
        elif choice == "00":
            in_notification_menu = False
        else:
            print(box("❌ Pilihan tidak valid.", ["Silakan coba lagi."], center=True))
            pause()