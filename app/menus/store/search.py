from app.client.store.search import get_family_list, get_store_packages
from app.menus.package import get_packages_by_family, show_package_details
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance

WIDTH = 55

def show_family_list_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
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
    in_family_list_menu = True
    while in_family_list_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        spinner("Fetching family list...")
        family_list_res = get_family_list(api_key, tokens, subs_type, is_enterprise)
        if not family_list_res:
            print(box("INFO", ["No family list found."], yellow))
            in_family_list_menu = False
            continue
        
        family_list = family_list_res.get("data", {}).get("results", [])
        
        clear_screen()
        term_width = shutil.get_terminal_size((80, 20)).columns
        print(f"{gray}┌{'─' * (term_width - 2)}┐{reset}")
        title = "FAMILY LIST"
        pad_total = term_width - 2 - len(title)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        print(f"{gray}│{reset}{' ' * pad_left}{cyan}{title}{reset}{' ' * pad_right}{gray}│{reset}")
        print(f"{gray}└{'─' * (term_width - 2)}┘{reset}\n")

        for i, family in enumerate(family_list):
            family_name = family.get("label", "N/A")
            family_code = family.get("id", "N/A")

            lines = [
                f"{green}{i + 1}.{reset} {yellow}{family_name}{reset}",
                f"Family Code: {cyan}{family_code}{reset}"
            ]
            print(box("", lines, color=white))
        
        print(box("OPTIONS", [
            f"{green}00.{reset} Back to Main Menu",
            "Input the number to view packages in that family."
        ], color=white))

        choice = bordered_input("Enter your choice:")
        if choice == "00":
            in_family_list_menu = False

        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(family_list):
            selected_family = family_list[int(choice) - 1]
            family_code = selected_family.get("id", "")
            family_name = selected_family.get("label", "N/A")
            spinner(f"Fetching packages for family: {family_name}...")
            get_packages_by_family(family_code)
    
    pause()


def show_store_packages_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
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
    in_store_packages_menu = True
    while in_store_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        spinner("Fetching store packages...")
        store_packages_res = get_store_packages(api_key, tokens, subs_type, is_enterprise)
        if not store_packages_res:
            print(box("INFO", ["No store packages found."], yellow))
            in_store_packages_menu = False
            continue
        
        store_packages = store_packages_res.get("data", {}).get("results_price_only", [])
        
        clear_screen()
        term_width = shutil.get_terminal_size((80, 20)).columns
        print(f"{gray}┌{'─' * (term_width - 2)}┐{reset}")
        title = "STORE PACKAGES"
        pad_total = term_width - 2 - len(title)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        print(f"{gray}│{reset}{' ' * pad_left}{cyan}{title}{reset}{' ' * pad_right}{gray}│{reset}")
        print(f"{gray}└{'─' * (term_width - 2)}┘{reset}\n")

        packages = {}
        for i, package in enumerate(store_packages):
            title_pkg = package.get("title", "N/A")
            original_price = package.get("original_price", 0)
            discounted_price = package.get("discounted_price", 0)
            price = discounted_price if discounted_price > 0 else original_price
            validity = package.get("validity", "N/A")
            family_name = package.get("family_name", "N/A")

            action_type = package.get("action_type", "")
            action_param = package.get("action_param", "")

            packages[f"{i + 1}"] = {
                "action_type": action_type,
                "action_param": action_param
            }

            lines = [
                f"{green}{i + 1}.{reset} {yellow}{title_pkg}{reset}",
                f"Family: {cyan}{family_name}{reset}",
                f"Price: Rp{price}",
                f"Validity: {validity}"
            ]
            print(box("", lines, color=white))
        
        print(box("OPTIONS", [
            f"{green}00.{reset} Back to Main Menu",
            "Input the number to view package details."
        ], color=white))

        choice = bordered_input("Enter your choice:")
        if choice == "00":
            in_store_packages_menu = False
        elif choice in packages:
            selected_package = packages[choice]
            action_type = selected_package["action_type"]
            action_param = selected_package["action_param"]
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
        else:
            print(box("INVALID", ["Invalid choice. Please enter a valid package number."], red))
            pause()