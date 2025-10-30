import requests

from app.client.engsel import get_family, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.client.ewallet import show_multipayment
from app.client.qris import show_qris_payment
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem

def show_hot_menu():
    import requests, sys, shutil, time, re, textwrap

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🔧 Fungsi utilitas visual
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(text, width): return textwrap.wrap(text, width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        pad_space = inner_width - visible_len(text)
        if pad_space < 0: pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 1)}{gray}│{reset}"

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
            for c in content_lines: body.append(box_line(c, color))
        return "\n".join([top] + body + [bottom])

    def spinner(text="Memuat..."):
        anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        for i in range(15):
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

    # ======== KODE ASLI MULAI (TIDAK DIUBAH SEDIKITPUN) ========
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print(box("PAKET HOT V1", [], center=True))
        spinner("Mengambil data paket hot...")

        url = "https://me.mashu.lol/pg-hot.json"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(box("FAILED", ["Gagal mengambil data hot package."], red))
            pause()
            return None

        hot_packages = response.json()
        print(box("DAFTAR HOT PACKAGE", [], center=True))

        for idx, p in enumerate(hot_packages):
            lines = [
                f"{red}Family{reset}: {yellow}{p['family_name']}{reset}",
                f"{red}Variant{reset}: {cyan}{p['variant_name']}{reset}",
                f"{red}Option{reset}: {green}{p['option_name']}{reset}"
            ]
            print(box(f"{idx + 1}. HOT PACKAGE", lines))

        print(box("", [f"{green}00.{reset} Kembali ke menu utama"]))

        choice = bordered_input("Pilih paket (nomor):")
        if choice == "00":
            in_bookmark_menu = False
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]
            
            print(box("DETAIL", [f"Mengambil data family untuk {selected_bm['family_name']}..."], cyan))
            spinner("Loading family data")
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print(box("FAILED", ["Gagal mengambil data family."], red))
                pause()
                continue
            
            package_variants = family_data["package_variants"]
            option_code = None
            for variant in package_variants:
                if variant["name"] == selected_bm["variant_name"]:
                    selected_variant = variant
                    package_options = selected_variant["package_options"]
                    for option in package_options:
                        if option["order"] == selected_bm["order"]:
                            selected_option = option
                            option_code = selected_option["package_option_code"]
                            break
            
            if option_code:
                print(box("PROCESSING", [f"Menampilkan detail paket: {selected_bm['option_name']}"], yellow))
                spinner("Fetching details")
                show_package_details(api_key, tokens, option_code, is_enterprise)
        else:
            print(box("INVALID", ["Input tidak valid. Silahkan coba lagi."], red))
            pause()
            continue

def show_hot_menu2():
    import requests, sys, shutil, time, re, textwrap

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🔧 Utilitas tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(text, width): return textwrap.wrap(text, width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        pad_space = inner_width - visible_len(text)
        if pad_space < 0: pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 1)}{gray}│{reset}"

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
        for i in range(12):
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

    # ======== KODE ASLI MULAI (TIDAK DIUBAH SEDIKITPUN) ========
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print(box("PAKET HOT V2", [], center=True))
        spinner("Mengambil data hot package...")

        url = "https://me.mashu.lol/pg-hot2.json"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(box("FAILED", ["Gagal mengambil data hot package."], red))
            pause()
            return None

        hot_packages = response.json()
        print(box("DAFTAR HOT PACKAGE", [], center=True))

        for idx, p in enumerate(hot_packages):
            lines = [
                f"{red}Nama Paket{reset}: {yellow}{p['name']}{reset}",
                f"{red}Harga{reset}: {green}{p['price']}{reset}"
            ]
            print(box(f"{idx + 1}. HOT PACKAGE", lines))

        print(box("", [f"{green}00.{reset} Kembali ke menu utama"]))
        choice = bordered_input("Pilih paket (nomor):")

        if choice == "00":
            in_bookmark_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                print(box("EMPTY", ["Paket tidak tersedia."], yellow))
                pause()
                continue
            
            payment_items = []
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )
                
                # Force failed when one of the package detail is None
                if not package_detail:
                    print(box("FAILED", [f"Gagal mengambil detail paket untuk {package['family_code']}."], red))
                    return None
                
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            clear_screen()
            term_width = shutil.get_terminal_size((80, 20)).columns
            wrap_width = term_width - 10

            # ✨ Detail yang panjang dibungkus agar rapi
            detail_lines = [
                f"{red}Name{reset}: {yellow}{selected_package['name']}{reset}",
                f"{red}Price{reset}: {green}{selected_package['price']}{reset}",
                f"{red}Detail{reset}:"
            ]
            for line in wrap_text(selected_package['detail'], wrap_width):
                detail_lines.append(f"  {cyan}{line}{reset}")

            supported_payment = selected_package.get("supported_payment", "E-wallet & QRIS.")
            detail_lines.append(f"{red}Supported payment{reset}: {green}{supported_payment}{reset}")
            print(box("DETAIL PAKET", detail_lines))

            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                print(box("METODE PEMBELIAN", [
                    f"{cyan}1.{reset} Balance",
                    f"{cyan}2.{reset} E-Wallet",
                    f"{cyan}3.{reset} QRIS",
                    f"{green}00.{reset} Kembali ke menu sebelumnya"
                ]))
                
                input_method = bordered_input("Pilih metode (nomor):")

                if input_method == "1":
                    if overwrite_amount == -1:
                        print(box("KONFIRMASI", [
                            f"Pastikan sisa balance KURANG DARI Rp{payment_items[-1]['item_price']}!!!"
                        ], yellow))
                        balance_answer = bordered_input("Apakah anda yakin ingin melanjutkan pembelian? (y/n):")
                        if balance_answer.lower() != "y":
                            print(box("CANCELLED", ["Pembelian dibatalkan oleh user."], red))
                            pause()
                            in_payment_menu = False
                            continue

                    spinner("Memproses pembelian...")
                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount=overwrite_amount,
                        token_confirmation_idx=token_confirmation_idx,
                        amount_idx=amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False

                elif input_method == "2":
                    spinner("Membuka menu E-Wallet...")
                    show_multipayment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False

                elif input_method == "3":
                    spinner("Membuka QRIS Payment...")
                    show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False

                elif input_method == "00":
                    in_payment_menu = False
                    continue
                else:
                    print(box("INVALID", ["Metode tidak valid. Silahkan coba lagi."], red))
                    pause()
                    continue
        else:
            print(box("INVALID", ["Input tidak valid. Silahkan coba lagi."], red))
            pause()
            continue