import json
from app.client.store.segments import get_segments
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.menus.package import show_package_details

WIDTH = 55

def show_store_segments_menu(is_enterprise: bool = False):
    import sys, time, shutil, re, textwrap

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🔧 Utilitas Tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(text, width): return textwrap.wrap(text, width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        pad_space = inner_width - visible_len(text)
        if pad_space < 0: pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * pad_space} {gray}│{reset}"

    def box(title="", content_lines=None, color=white, center=False):
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
        for i in range(10):
            sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
            sys.stdout.flush(); time.sleep(0.07)
        sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

    def bordered_input(prompt_text):
        term_width = shutil.get_terminal_size((80, 20)).columns
        top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
        left = f"{gray}│{reset} {cyan}{prompt_text}{reset} "
        sys.stdout.write(top + "\n" + left)
        user_input = input()
        return user_input.strip()

    # ============================================================
    # 🧱 KODE ASLI DIMULAI (TIDAK DIUBAH SEDIKITPUN)
    # ============================================================
    in_store_segments_menu = True
    while in_store_segments_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()

        spinner("Fetching store segments...")
        segments_res = get_segments(api_key, tokens, is_enterprise)
        if not segments_res:
            print(box("INFO", ["No segments found."], yellow))
            in_store_segments_menu = False
            continue

        segments = segments_res.get("data", {}).get("store_segments", [])

        clear_screen()

        # 🧭 Header Center
        term_width = shutil.get_terminal_size((80, 20)).columns
        print(f"{gray}┌{'─' * (term_width - 2)}┐{reset}")
        title = "STORE SEGMENTS"
        pad_total = term_width - 2 - len(title)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        print(f"{gray}│{reset}{' ' * pad_left}{cyan}{title}{reset}{' ' * pad_right}{gray}│{reset}")
        print(f"{gray}└{'─' * (term_width - 2)}┘{reset}\n")

        packages = {}
        for i, segment in enumerate(segments):
            name = segment.get("title", "N/A")
            banners = segment.get("banners", [])

            letter = chr(65 + i)  # A, B, C...
            segment_header = [f"{green}Banner {letter}{reset}: {yellow}{name}{reset}", f"Jumlah Banner: {len(banners)}"]
            print(box("SEGMENT", segment_header, color=white))

            for j, banner in enumerate(banners):
                discounted_price = banner.get("discounted_price", "N/A")
                title = banner.get("title", "N/A")
                validity = banner.get("validity", "N/A")
                family_name = banner.get("family_name", "N/A")

                action_param = banner.get("action_param", "")
                action_type = banner.get("action_type", "")

                packages[f"{letter.lower()}{j + 1}"] = {
                    "action_param": action_param,
                    "action_type": action_type
                }

                lines = [
                    f"{cyan}{letter}{j + 1}.{reset} {green}{family_name}{reset} - {yellow}{title}{reset}",
                    f"Price: Rp{discounted_price}",
                    f"Validity: {validity}",
                    f"Action Type: {action_type}"
                ]
                print(box("", lines, color=white))

        print(box("OPTIONS", [
            f"{green}00.{reset} Back to Main Menu",
            f"Masukkan kode (contoh: A1, B2) untuk melihat detail paket"
        ], color=white))

        choice = bordered_input("Enter your choice:")
        if choice == "00":
            in_store_segments_menu = False
            continue

        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            print(box("INVALID", ["Invalid choice. Please enter a valid package code."], red))
            pause()
            continue

        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]

        if action_type == "PDP":
            _ = show_package_details(
                api_key,
                tokens,
                action_param,
                is_enterprise
            )
        else:
            print(box("UNHANDLED ACTION", [
                f"Action Type: {action_type}",
                f"Param: {action_param}"
            ], yellow))
            pause()