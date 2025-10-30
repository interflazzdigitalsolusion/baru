from app.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.package import show_package_details, get_packages_by_family
from datetime import datetime

WIDTH = 55

def show_redeemables_menu(is_enterprise: bool = False):
    import sys, time, shutil, re, textwrap

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🔧 Utilitas Tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
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

    # =====================================================
    # 🧱 KODE ASLI DIMULAI (TIDAK DIUBAH SEDIKITPUN)
    # =====================================================
    in_redeemables_menu = True
    while in_redeemables_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        spinner("Fetching redeemables...")
        redeemables_res = get_redeemables(api_key, tokens, is_enterprise)
        if not redeemables_res:
            print(box("INFO", ["No redeemables found."], yellow))
            in_redeemables_menu = False
            continue
        
        categories = redeemables_res.get("data", {}).get("categories", [])
        
        clear_screen()
        term_width = shutil.get_terminal_size((80, 20)).columns
        print(f"{gray}┌{'─' * (term_width - 2)}┐{reset}")
        title = "REDEEMABLES"
        pad_total = term_width - 2 - len(title)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        print(f"{gray}│{reset}{' ' * pad_left}{cyan}{title}{reset}{' ' * pad_right}{gray}│{reset}")
        print(f"{gray}└{'─' * (term_width - 2)}┘{reset}\n")
        
        packages = {}
        for i, category in enumerate(categories):
            category_name = category.get("category_name", "N/A")
            category_code = category.get("category_code", "N/A")
            redemables = category.get("redeemables", [])
            
            letter = chr(65 + i)
            lines = [
                f"{green}{letter}.{reset} Category: {yellow}{category_name}{reset}",
                f"Code: {cyan}{category_code}{reset}",
                f"Total Redeemables: {len(redemables)}"
            ]
            print(box("CATEGORY", lines, color=white))
            
            if len(redemables) == 0:
                print(box("", ["No redeemables in this category."], color=yellow))
                continue
            
            for j, redemable in enumerate(redemables):
                name = redemable.get("name", "N/A")
                valid_until = redemable.get("valid_until", 0)
                valid_until_date = datetime.strftime(
                    datetime.fromtimestamp(valid_until), "%Y-%m-%d"
                )
                
                action_param = redemable.get("action_param", "")
                action_type = redemable.get("action_type", "")
                
                packages[f"{letter.lower()}{j + 1}"] = {
                    "action_param": action_param,
                    "action_type": action_type
                }
                
                details = [
                    f"{cyan}{letter}{j + 1}.{reset} {green}{name}{reset}",
                    f"Valid Until: {yellow}{valid_until_date}{reset}",
                    f"Action Type: {cyan}{action_type}{reset}"
                ]
                print(box("", details, color=white))
        
        print(box("OPTIONS", [
            f"{green}00.{reset} Back",
            f"Enter your choice (e.g., A1, B2) to view details."
        ], color=white))
        
        choice = bordered_input("Enter your choice:")
        if choice == "00":
            in_redeemables_menu = False
            continue
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            print(box("INVALID", ["Invalid choice. Please enter a valid package code."], red))
            pause()
            continue
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PLP":
            get_packages_by_family(action_param, is_enterprise, "")
        elif action_type == "PDP":
            show_package_details(
                api_key,
                tokens,
                action_param,
                is_enterprise,
            )
        else:
            print(box("UNHANDLED ACTION", [
                f"Action type: {action_type}",
                f"Param: {action_param}"
            ], yellow))
            pause()