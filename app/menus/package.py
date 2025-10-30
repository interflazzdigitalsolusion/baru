import json
import sys

import requests
from app.service.auth import AuthInstance
from app.client.engsel import get_auth_code, get_family, get_package, get_addons, get_package_details, send_api_request
from app.client.engsel2 import unsubscribe
from app.service.bookmark import BookmarkInstance
from app.client.purchase import settlement_bounty, settlement_loyalty, bounty_allotment
from app.menus.util import clear_screen, pause, display_html
from app.client.qris import show_qris_payment
from app.client.ewallet import show_multipayment
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.menus.util import format_quota_byte
from app.service.decoy import DecoyInstance

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    import sys, time, json, shutil, re, textwrap, requests

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
        for i in range(12):
            sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
            sys.stdout.flush()
            time.sleep(0.07)
        sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

    def bordered_input(prompt_text):
        term_width = shutil.get_terminal_size((80, 20)).columns
        top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
        left = f"{gray}│{reset} {cyan}{prompt_text}{reset} "
        sys.stdout.write(top + "\n" + left)
        user_input = input()
        return user_input.strip()

    # ==========================================================
    # ===============  KODE ASLI DIMULAI  ======================
    # ==========================================================
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "")

    clear_screen()
    print(box("DETAIL PAKET", [], center=True))
    spinner("Mengambil detail paket...")

    package = get_package(api_key, tokens, package_option_code)
    if not package:
        print(box("FAILED", ["Failed to load package details."], red))
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","")
    family_name = package.get("package_family", {}).get("name","")
    variant_name = package.get("package_detail_variant", "").get("name","")
    title = f"{family_name} - {variant_name} - {option_name}".strip()
    
    family_code = package.get("package_family", {}).get("package_family_code","")
    parent_code = package.get("package_addon", {}).get("parent_code","") or "N/A"

    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]

    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]

# ✨ tampilkan informasi utama
    info_lines = [
        f"{red}Nama{reset}: {yellow}{title}{reset}",
        f"{red}Harga{reset}: {green}Rp {price}{reset}",
        f"{red}Payment For{reset}: {cyan}{payment_for}{reset}",
        f"{red}Masa Aktif{reset}: {yellow}{validity}{reset}",
        f"{red}Point{reset}: {green}{package['package_option']['point']}{reset}",
        f"{red}Plan Type{reset}: {cyan}{package['package_family']['plan_type']}{reset}",
        "",
        f"{red}Family Code{reset}: {yellow}{family_code}{reset}",
        f"{red}Parent Code{reset}: {cyan}{parent_code}{reset}"
    ]
    
    # --- tambahan agar teks panjang otomatis turun ke baris baru dan tampil dalam border rapi ---
    import textwrap, shutil, re
    term_width = shutil.get_terminal_size((80, 20)).columns
    max_width = term_width - 6

    wrapped_info_lines = []
    for line in info_lines:
        clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
        if len(clean) > max_width:
            parts = textwrap.wrap(line, width=max_width)
            wrapped_info_lines.extend(parts)
        else:
            wrapped_info_lines.append(line)

    gray = "\033[90m"
    reset = "\033[0m"
    top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
    bottom = f"{gray}└{'─' * (term_width - 2)}┘{reset}"

    print(top)
    for line in wrapped_info_lines:
        clean_len = len(re.sub(r'\x1b\[[0-9;]*m', '', line))
        pad = term_width - clean_len - 4
        if pad < 0:
            pad = 0
        print(f"{gray}│{reset} {line}{' ' * pad}{gray}│{reset}")
    print(bottom)

    # ===================== BENEFITS ===========================
    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        print(box("BENEFITS", [], center=True))
        for benefit in benefits:
            b_lines = [
                f"{green}Name{reset}: {benefit['name']}",
                f" Item ID: {benefit['item_id']}"
            ]
            data_type = benefit['data_type']
            if data_type == "VOICE" and benefit['total'] > 0:
                b_lines.append(f" Total: {benefit['total']/60} menit")
            elif data_type == "TEXT" and benefit['total'] > 0:
                b_lines.append(f" Total: {benefit['total']} SMS")
            elif data_type == "DATA" and benefit['total'] > 0:
                quota = int(benefit['total'])
                if quota >= 1_000_000_000:
                    quota_gb = quota / (1024 ** 3)
                    b_lines.append(f" Quota: {quota_gb:.2f} GB")
                elif quota >= 1_000_000:
                    quota_mb = quota / (1024 ** 2)
                    b_lines.append(f" Quota: {quota_mb:.2f} MB")
                elif quota >= 1_000:
                    quota_kb = quota / 1024
                    b_lines.append(f" Quota: {quota_kb:.2f} KB")
                else:
                    b_lines.append(f" Total: {quota}")
            elif data_type not in ["DATA", "VOICE", "TEXT"]:
                b_lines.append(f" Total: {benefit['total']} ({data_type})")

            if benefit["is_unlimited"]:
                b_lines.append(f"{yellow}Unlimited: Yes{reset}")
            print(box("", b_lines))
            
            # ===================== ADDONS ============================
    spinner("Mengambil data addons...")
    addons = get_addons(api_key, tokens, package_option_code)
    bonuses = addons.get("bonuses", [])

    addon_lines = []
    if addons:
        addon_lines.append(f"{green}{reset}")

        if bonuses:
            for bonus in bonuses:
                addon_lines.append(f"Nama: {bonus.get('name', '-')}")
                addon_lines.append(f"Family: {bonus.get('family_name', '-')}")
                addon_lines.append(f"Validity: {bonus.get('validity', '-')}")
                addon_lines.append(f"Info: {bonus.get('benefit_information', '-')}")
                addon_lines.append("")  # pemisah antar item
        else:
            # tampilkan struktur default ketika semua kosong
            addon_lines.append("addons: []")
            addon_lines.append("bonuses: []")
            addon_lines.append(f"force_to_hide_bonus: {addons.get('force_to_hide_bonus', False)}")
            addon_lines.append(f"paid_bonuses: {addons.get('paid_bonuses', [])}")
            addon_lines.append(f"parent_code: {addons.get('parent_code', '')}")
            addon_lines.append(f"upsell: {addons.get('upsell', [])}")
    else:
        addon_lines.append(f"{red}Tidak ada addons ditemukan.{reset}")

    print(box("ADDONS INFORMATION", addon_lines))

    # ===================== S&K ===============================
    

    # --- tambahan border untuk versi print langsung dengan pembungkus otomatis ---
    term_width = shutil.get_terminal_size((80, 20)).columns
    gray = "\033[90m"
    reset = "\033[0m"
    top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
    bottom = f"{gray}└{'─' * (term_width - 2)}┘{reset}"
    title = f"{gray}│ {cyan}S&K MyXL{reset}{' ' * (term_width - 11)}{gray}│{reset}"

    print(top)
    print(title)

    import textwrap
    max_width = term_width - 3  # ruang dalam border

    for line in detail.split("\n"):
        # pisahkan teks panjang menjadi beberapa baris agar tetap dalam batas border
        wrapped_lines = textwrap.wrap(line.strip(), width=max_width)
        if not wrapped_lines:
            wrapped_lines = [""]
        for wl in wrapped_lines:
            pad = max_width - len(wl)
            print(f"{gray}│{reset} {wl}{' ' * pad}{gray}│{reset}")
    print(bottom)
    
    # ===================== MENU OPSI =========================
    in_package_detail_menu = True
    while in_package_detail_menu:
        print(box("OPTIONS", [
            f"{cyan}1.{reset} Beli dengan Pulsa",
            f"{cyan}2.{reset} Beli dengan E-Wallet",
            f"{cyan}3.{reset} Bayar dengan QRIS",
            f"{cyan}4.{reset} Pulsa + Decoy",
            f"{cyan}5.{reset} Pulsa + Decoy V2",
            f"{cyan}6.{reset} QRIS + Decoy (+1K)",
            f"{cyan}7.{reset} QRIS + Decoy V2",
            f"{cyan}8.{reset} Pulsa N kali",
            f"{green}00.{reset} Kembali ke daftar paket"
        ]))

        if payment_for == "":
            payment_for = "BUY_PACKAGE"
        if payment_for == "REDEEM_VOUCHER":
            print(box("", [
                f"{yellow}B.{reset} Ambil sebagai bonus",
                f"{yellow}BA.{reset} Kirim bonus",
                f"{yellow}L.{reset} Beli dengan Poin"
            ]))

        if option_order != -1:
            print(box("", [f"{green}0.{reset} Tambah ke Bookmark"]))

        choice = bordered_input("Pilihan:")
        if choice == "00":
            return False

        elif choice == "0" and option_order != -1:
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print(box("BOOKMARK", ["Paket berhasil ditambahkan ke bookmark."], green))
            else:
                print(box("BOOKMARK", ["Paket sudah ada di bookmark."], yellow))
            pause()
            continue

        elif choice == '1':
            settlement_balance(api_key, tokens, payment_items, payment_for, True)
            input(box("INFO", ["Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali."], cyan))
            return True

        elif choice == '2':
            show_multipayment(api_key, tokens, payment_items, payment_for, True)
            input(box("INFO", ["Silahkan lakukan pembayaran & cek hasil pembelian di MyXL. Tekan Enter untuk kembali."], cyan))
            return True

        elif choice == '3':
            show_qris_payment(api_key, tokens, payment_items, payment_for, True)
            input(box("INFO", ["Silahkan lakukan pembayaran & cek hasil pembelian di MyXL. Tekan Enter untuk kembali."], cyan))
            return True

        elif choice == '4' or choice == '5':
            decoy = DecoyInstance.get_decoy("balance")
            spinner("Mengambil data decoy...")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
            if not decoy_package_detail:
                print(box("FAILED", ["Failed to load decoy package details."], red))
                pause()
                return False

            payment_items.append(PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            ))

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            idx = 1 if choice == '5' else 0
            res = settlement_balance(
                api_key, tokens, payment_items,
                "🤫", False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=idx
            )
            if res and res.get("status", "") != "SUCCESS":
                msg = res.get("message", "")
                if "Bizz-err.Amount.Total" in msg:
                    amt = int(msg.split("=")[1].strip())
                    print(box("ADJUST", [f"Adjusted total amount to: {amt}"], yellow))
                    res = settlement_balance(api_key, tokens, payment_items, "🤫", False,
                        overwrite_amount=amt, token_confirmation_idx=-1)
                    if res.get("status") == "SUCCESS":
                        print(box("SUCCESS", ["Purchase successful!"], green))
            else:
                print(box("SUCCESS", ["Purchase successful!"], green))
            pause()
            return True

        elif choice == '6' or choice == '7':
            decoy_type = "qris" if choice == '6' else "qris0"
            decoy = DecoyInstance.get_decoy(decoy_type)
            spinner("Mengambil data decoy QRIS...")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
            if not decoy_package_detail:
                print(box("FAILED", ["Failed to load decoy package details."], red))
                pause()
                return False

            payment_items.append(PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            ))

            info_lines = [
                f"Harga Utama: Rp {price}",
                f"Harga Decoy: Rp {decoy_package_detail['package_option']['price']}",
                "Silahkan sesuaikan amount (trial & error, 0 = malformed)"
            ]
            print(box("QRIS DECOY INFO", info_lines))
            show_qris_payment(
                api_key, tokens, payment_items, "SHARE_PACKAGE", True, token_confirmation_idx=1
            )
            input(box("INFO", ["Silahkan lakukan pembayaran & cek hasil pembelian di MyXL. Tekan Enter untuk kembali."], cyan))
            return True

        elif choice == '8':
            use_decoy_for_n_times = bordered_input("Use decoy package? (y/n):").lower() == 'y'
            n_times_str = bordered_input("Jumlah pembelian (contoh: 3):")
            delay_str = bordered_input("Delay antar pembelian (detik):")
            if not delay_str.isdigit(): delay_str = "0"
            try:
                n_times = int(n_times_str)
                if n_times < 1: raise ValueError()
            except ValueError:
                print(box("INVALID", ["Jumlah harus angka >= 1"], red))
                pause(); continue

            purchase_n_times_by_option_code(
                n_times, option_code=package_option_code,
                use_decoy=use_decoy_for_n_times,
                delay_seconds=int(delay_str),
                pause_on_success=False,
                token_confirmation_idx=1
            )

        elif choice.lower() == 'b':
            settlement_bounty(
                api_key, tokens, token_confirmation, ts_to_sign,
                payment_target=package_option_code, price=price, item_name=variant_name
            )
            input(box("INFO", ["Silahkan lakukan pembayaran & cek hasil pembelian di MyXL."], cyan))
            return True

        elif choice.lower() == 'ba':
            destination_msisdn = bordered_input("Nomor tujuan bonus (62...):")
            bounty_allotment(
                api_key=api_key, tokens=tokens, ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name, item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            pause(); return True

        elif choice.lower() == 'l':
            settlement_loyalty(
                api_key=api_key, tokens=tokens,
                token_confirmation=token_confirmation, ts_to_sign=ts_to_sign,
                payment_target=package_option_code, price=price,
            )
            input(box("INFO", ["Silahkan lakukan pembayaran & cek hasil pembelian di MyXL."], cyan))
            return True

        else:
            print(box("CANCELLED", ["Purchase cancelled."], yellow))
            return False

    pause()
    sys.exit(0)

def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    import sys, time, shutil, re, textwrap

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🔧 Utilitas tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(text, width): return textwrap.wrap(str(text), width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        visible_length = visible_len(text)
        pad_space = inner_width - visible_length
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
                for wrapped in wrap_text(c, term_width - 10):
                    body.append(box_line(wrapped, color))
        return "\n".join([top] + body + [bottom])

    def spinner(text="Memuat..."):
        anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        for i in range(10):
            sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

    def bordered_input(prompt_text):
        term_width = shutil.get_terminal_size((80, 20)).columns
        top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
        left = f"{gray}│{reset} {cyan}{prompt_text}{reset} "
        sys.stdout.write(top + "\n" + left)
        user_input = input()
        return user_input.strip()

    # ========== KODE ASLI (TIDAK DIUBAH SEDIKITPUN) ==========
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print(box("⚠️ TOKEN ERROR", ["No active user tokens found."], red))
        pause()
        return None
    
    packages = []
    
    data = get_family(
        api_key,
        tokens,
        family_code,
        is_enterprise,
        migration_type
    )
    
    if not data:
        print(box("FAILED", ["Failed to load family data."], red))
        pause()
        return None

    price_currency = "Rp"
    rc_bonus_type = data["package_family"].get("rc_bonus_type", "")
    if rc_bonus_type == "MYREWARDS":
        price_currency = "Poin"
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        spinner("Loading family info")
        wrap_width = shutil.get_terminal_size((80, 20)).columns - 10

        # FAMILY INFO BOX
        family_info = [
            f"{red}Family Name{reset}: {yellow}{data['package_family']['name']}{reset}",
            f"{red}Family Code{reset}:",
        ]
        for line in wrap_text(family_code, wrap_width):
            family_info.append(f"  {cyan}{line}{reset}")
        family_info.append(f"{red}Family Type{reset}: {yellow}{data['package_family']['package_family_type']}{reset}")
        family_info.append(f"{red}Variant Count{reset}: {yellow}{len(data['package_variants'])}{reset}")
        print(box("FAMILY INFORMATION", family_info, white))

        # HEADER PAKET
        print(box("PAKET TERSEDIA", [], center=True))

        package_variants = data["package_variants"]
        option_number = 1
        variant_number = 1
        
        for variant in package_variants:
            variant_name = variant["name"]
            variant_code = variant["package_variant_code"]
            variant_info = [
                f"{red}Variant {variant_number}{reset}: {yellow}{variant_name}{reset}",
                f"{red}Code{reset}:"
            ]
            for line in wrap_text(variant_code, wrap_width):
                variant_info.append(f"  {cyan}{line}{reset}")
            print(box("", variant_info, white))

            for option in variant["package_options"]:
                option_name = option["name"]
                price_line = f"{cyan}{option_number}. {option_name}{reset} - {yellow}{price_currency} {option['price']}{reset}"
                print(box_line(price_line))
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })
                option_number += 1
            
            if variant_number < len(package_variants):
                print(box_line("-" * (wrap_width // 2), gray))
            variant_number += 1
        
        print(box("", [f"{green}00.{reset} Kembali ke menu utama"], white))

        pkg_choice = bordered_input("Pilih paket (nomor):")
        if pkg_choice == "00":
            in_package_menu = False
            return None
        
        if isinstance(pkg_choice, str) == False or not pkg_choice.isdigit():
            print(box("INVALID", ["Input tidak valid. Silakan masukan nomor paket."], red))
            continue
        
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        
        if not selected_pkg:
            print(box("NOT FOUND", ["Paket tidak ditemukan. Silakan masukan nomor yang benar."], red))
            continue
        
        print(box("DETAIL", [f"Menampilkan detail paket {selected_pkg['option_name']}..."], cyan))
        spinner("Fetching details")
        show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"],
        )
        
    return packages
    
def fetch_my_packages():
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    def visible_len(s):
        import re
        return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

    def wrap_text(text, width):
        import textwrap
        return textwrap.wrap(text, width=width)

    def box_line(text="", color=white):
        import shutil
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        visible_length = visible_len(text)
        pad_space = inner_width - visible_length
        if pad_space < 0:
            pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 1)}{gray}│{reset}"

    def box(title="", content_lines=None, color=white, center=False):
        import shutil
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
        import sys, time
        anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        for i in range(15):
            sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
            sys.stdout.flush()
            time.sleep(0.07)
        sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

    # ======== KODE ASLI MULAI (TIDAK DIUBAH SEDIKITPUN) ========
    in_my_packages_menu = True
    while in_my_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            print(box("⚠️ TOKEN ERROR", ["No active user tokens found."], red))
            pause()
            return None
        
        id_token = tokens.get("id_token")
        path = "api/v8/packages/quota-details"
        payload = {
            "is_enterprise": False,
            "lang": "en",
            "family_member_id": ""
        }
        
        print(box("FETCHING", ["Fetching my packages..."], cyan))
        spinner("Requesting package data")
        res = send_api_request(api_key, path, payload, id_token, "POST")
        if res.get("status") != "SUCCESS":
            print(box("FAILED", ["Failed to fetch packages", f"Response: {res}"], red))
            pause()
            return None
        
        quotas = res["data"]["quotas"]
        clear_screen()
        print(box("MY PACKAGES", [], center=True))
        my_packages = []
        num = 1
        for quota in quotas:
            quota_code = quota["quota_code"]
            group_code = quota["group_code"]
            group_name = quota["group_name"]
            quota_name = quota["name"]
            family_code = "N/A"
            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")
            
            benefit_infos = []
            benefits = quota.get("benefits", [])
            if len(benefits) > 0:
                for benefit in benefits:
                    benefit_id = benefit.get("id", "")
                    name = benefit.get("name", "")
                    data_type = benefit.get("data_type", "N/A")
                    # 🔥 Label merah, nilai kuning
                    benefit_info = [
                        f"{red}ID{reset}: {yellow}{benefit_id}{reset}",
                        f"{red}Name{reset}: {yellow}{name}{reset}",
                        f"{red}Type{reset}: {yellow}{data_type}{reset}"
                    ]
                    remaining = benefit.get("remaining", 0)
                    total = benefit.get("total", 0)
                    if data_type == "DATA":
                        remaining_str = format_quota_byte(remaining)
                        total_str = format_quota_byte(total)
                        benefit_info.append(f"{red}Kuota{reset}: {yellow}{remaining_str} / {total_str}{reset}")
                    elif data_type == "VOICE":
                        benefit_info.append(f"{red}Kuota{reset}: {yellow}{remaining/60:.2f} / {total/60:.2f} menit{reset}")
                    elif data_type == "TEXT":
                        benefit_info.append(f"{red}Kuota{reset}: {yellow}{remaining} / {total} SMS{reset}")
                    else:
                        benefit_info.append(f"{red}Kuota{reset}: {yellow}{remaining} / {total}{reset}")
                    benefit_infos.extend(benefit_info)
            
            print(box(f"Fetching package no. {num} details...", [], yellow))
            spinner(f"Loading package {num}")
            package_details = get_package(api_key, tokens, quota_code)
            if package_details:
                family_code = package_details["package_family"]["package_family_code"]

            # 🔥 Bungkus quota_code ke baris baru bila kepanjangan
            import shutil
            wrap_width = shutil.get_terminal_size((80, 20)).columns - 10
            wrapped_quota_code = wrap_text(quota_code, wrap_width)

            info_lines = [
                f"{white}Package {num}{reset}",
                f"Name: {cyan}{quota_name}{reset}",
                f"Group: {yellow}{group_name}{reset}",
                f"Quota Code:{reset}",
            ]
            info_lines.extend([f"  {cyan}{line}{reset}" for line in wrapped_quota_code])
            info_lines.extend([
                f"Family Code: {green}{family_code}{reset}",
                f"Group Code: {cyan}{group_code}{reset}",
            ])
            if benefit_infos:
                info_lines.append("Benefits:")
                info_lines.extend(["  " + b for b in benefit_infos])
            print(box("", info_lines))
            
            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })
            num += 1

        footer = [
            f"{cyan}Input package number to view detail.{reset}",
            f"{yellow}Input del <package number> to unsubscribe.{reset}",
            f"{green}Input 00 to return to main menu.{reset}"
        ]
        print(box("MENU", footer))

        choice = input(f"{cyan}Choice:{reset} ").strip()
        if choice == "00":
            in_my_packages_menu = False

        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(my_packages):
            selected_pkg = next((pkg for pkg in my_packages if pkg["number"] == int(choice)), None)
            if not selected_pkg:
                print(box("NOT FOUND", ["Paket tidak ditemukan. Silakan masukan nomor yang benar."], red))
                pause()
                continue
            _ = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
        
        elif choice.startswith("del "):
            del_parts = choice.split(" ")
            if len(del_parts) != 2 or not del_parts[1].isdigit():
                print(box("INVALID", ["Invalid input for delete command."], red))
                pause()
            
            del_number = int(del_parts[1])
            del_pkg = next((pkg for pkg in my_packages if pkg["number"] == del_number), None)
            if not del_pkg:
                print(box("NOT FOUND", ["Package not found for deletion."], red))
                pause()
            
            confirm = input(f"{yellow}Are you sure you want to unsubscribe from package {del_number}. {del_pkg['name']}? (y/n): {reset}")
            if confirm.lower() == 'y':
                print(box("UNSUBSCRIBE", [f"Unsubscribing from {del_pkg['name']}..."], yellow))
                spinner("Processing")
                success = unsubscribe(
                    api_key,
                    tokens,
                    del_pkg["quota_code"],
                    del_pkg["product_subscription_type"],
                    del_pkg["product_domain"]
                )
                if success:
                    print(box("SUCCESS ✅", ["Successfully unsubscribed from the package."], green))
                else:
                    print(box("FAILED ❌", ["Failed to unsubscribe from the package."], red))
            else:
                print(box("CANCELLED", ["Unsubscribe cancelled."], yellow))
            pause()