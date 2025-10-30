from dotenv import load_dotenv
from app.service.git import check_for_updates
load_dotenv()

import sys, json, shutil, re, time
from datetime import datetime
from itertools import cycle

from app.menus.util import clear_screen, pause
from app.client.engsel import get_balance
from app.client.engsel2 import get_tiering_info
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu

def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

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
    for i in range(15):
        sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

def input_box(prompt):
    gray, reset, cyan = "\033[90m", "\033[0m", "\033[96m"
    term_width = shutil.get_terminal_size((80, 20)).columns
    inner_width = term_width - 4
    text = f"{cyan}{prompt}{reset}"
    pad = inner_width - visible_len(prompt) - 3
    print(gray + "┌" + "─" * (term_width - 2) + "┐" + reset)
    sys.stdout.write(f"{gray}│{reset} {text} {cyan}")
    sys.stdout.flush()

def show_main_menu(profile):
    clear_screen()
    gray, reset, white, green, cyan, yellow = "\033[90m", "\033[0m", "\033[97m", "\033[92m", "\033[96m", "\033[93m"
    expired_at = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    label_width = 10
    value_pad = 25
    pts_text = profile['point_info'].replace('Points:', '').replace('Tier:', '').strip()
    pts_parts = re.split(r'\s+', pts_text)
    pts_value = pts_parts[0] if len(pts_parts) > 0 else ''
    tier_value = pts_parts[-1] if len(pts_parts) > 1 else ''
    info_lines = [
        f"{white}{'Nomor':<{label_width}}:{reset} {green}{profile['number']:<{value_pad}}{reset}{white}Type:{reset} {cyan}{profile['subscription_type']}{reset}",
        f"{white}{'Pulsa':<{label_width}}:{reset} {yellow}Rp {profile['balance']:<{value_pad-3}}{reset}{white}Aktif:{reset} {green}{expired_at}{reset}",
        f"{white}{'Points':<{label_width}}:{reset} {cyan}{pts_value:<{value_pad}}{reset}{white}Tier:{reset} {cyan}{tier_value}{reset}"
    ]
    print(box("", info_lines))
    print()
    left = [
        f"{cyan}1.{reset} Login/Ganti akun",
        f"{cyan}2.{reset} Lihat Paket Saya",
        f"{cyan}3.{reset} Buy Paket HOT-1",
        f"{cyan}4.{reset} Buy Paket HOT-2",
        f"{cyan}5.{reset} Buy Paket Option Code",
        f"{cyan}6.{reset} Buy Paket Family Code",
        f"{cyan}7.{reset} Buy LOOP Family Code"
    ]
    right = [
        f"{cyan}8.{reset} Riwayat Transaksi",
        f"{cyan}9.{reset} Family/Akrab Organizer",
        f"{cyan}10.{reset} [WIP] Circle",
        f"{cyan}11.{reset} Store Segments",
        f"{cyan}12.{reset} Store Family List",
        f"{cyan}13.{reset} Store Packages",
        f"{cyan}14.{reset} Redeemables"
    ]
    inner_width = shutil.get_terminal_size((80, 20)).columns - 6
    col = inner_width // 2
    menu_lines = []
    for i in range(max(len(left), len(right))):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        pad_l = col - visible_len(l)
        row = l + " " * pad_l + r
        menu_lines.append(row)
    print(box("", menu_lines))
    bottom = [
        f"{cyan}N.{reset} Notifikasi     {cyan}00.{reset} Bookmark Paket     {cyan}99.{reset} Tutup aplikasi"
    ]
    print(box("", bottom))
    input_box("Pilih menu:")

def main():
    while True:
        active = AuthInstance.get_active_user()
        if active:
            bal = get_balance(AuthInstance.api_key, active["tokens"]["id_token"])
            bal_remain = bal.get("remaining")
            bal_exp = bal.get("expired_at")
            tier = get_tiering_info(AuthInstance.api_key, active["tokens"]) if active["subscription_type"] == "PREPAID" else {}
            pts = f"Points: {tier.get('current_point', 0)} | Tier: {tier.get('tier', 0)}"
            profile = {
                "number": active["number"],
                "subscriber_id": active["subscriber_id"],
                "subscription_type": active["subscription_type"],
                "balance": bal_remain,
                "balance_expired_at": bal_exp,
                "point_info": pts
            }
            show_main_menu(profile)
            c = input().strip()
            if c == "1":
                u = show_account_menu()
                if u: AuthInstance.set_active_user(u)
            elif c == "2": fetch_my_packages()
            elif c == "3": show_hot_menu()
            elif c == "4": show_hot_menu2()
            elif c == "5":
                input_box("Masukkan Option Code (99 untuk batal):")
                oc = input().strip()
                if oc != "99": show_package_details(AuthInstance.api_key, active["tokens"], oc, False)
            elif c == "6":
                input_box("Masukkan Family Code (99 untuk batal):")
                fc = input().strip()
                if fc != "99": get_packages_by_family(fc)
            elif c == "7":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue

                start_from_option = input("Start purchasing from option number (default 1): ")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1

                use_decoy = input("Use decoy package? (y/n): ").lower() == 'y'
                pause_on_success = input("Pause on each successful purchase? (y/n): ").lower() == 'y'

                delay_seconds = input("Delay seconds between purchases (0 for no delay): ")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0

                purchase_by_family(
                    family_code,
                    use_decoy,
                    pause_on_success,
                    delay_seconds,
                    start_from_option
                )
    
            elif c == "8": show_transaction_history(AuthInstance.api_key, active["tokens"])
            elif c == "9": show_family_info(AuthInstance.api_key, active["tokens"])
            elif c == "10": show_circle_info(AuthInstance.api_key, active["tokens"])
            elif c == "11":
                input_box("Enterprise store? (y/n):")
                e = input().lower() == 'y'
                show_store_segments_menu(e)
            elif c == "12":
                input_box("Enterprise? (y/n):")
                e = input().lower() == 'y'
                show_family_list_menu(profile["subscription_type"], e)
            elif c == "13":
                input_box("Enterprise? (y/n):")
                e = input().lower() == 'y'
                show_store_packages_menu(profile["subscription_type"], e)
            elif c == "14":
                input_box("Enterprise? (y/n):")
                e = input().lower() == 'y'
                show_redeemables_menu(e)
            elif c == "00": show_bookmark_menu()
            elif c == "99":
                print(box("Keluar", ["Terima kasih telah menggunakan OpenAPI CLI."]))
                sys.exit(0)
            elif c.lower() == "n": show_notification_menu()
            elif c == "s": enter_sentry_mode()
            else:
                print(box("❌ Input tidak valid", ["Silakan coba lagi."]))
                pause()
        else:
            u = show_account_menu()
            if u: AuthInstance.set_active_user(u)

if __name__ == "__main__":
    try:
        print(box("Checking for updates...", []))
        spinner("Memeriksa update")
        if check_for_updates(): pause()
        main()
    except KeyboardInterrupt:
        print(box("Keluar", ["Program dihentikan."]))