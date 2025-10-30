import requests, time
from random import randint
from app.client.engsel import get_family, get_package_details, get_package
from app.menus.util import pause
from app.service.auth import AuthInstance
from app.service.decoy import DecoyInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance

# Purchase
def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    delay_seconds: int = 0,
    start_from_option: int = 1,
):
    import sys, time, shutil, re, json
    from random import randint

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🧩 Utilitas Tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(text, width): 
        import textwrap
        return textwrap.wrap(str(text), width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        pad_space = inner_width - visible_len(text)
        if pad_space < 0: pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 1)}{gray}│{reset}"

    def box(title="", lines=None, color=white, center=False):
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
        if lines:
            for line in lines:
                for wrapped in wrap_text(line, term_width - 10):
                    body.append(box_line(wrapped, color))
        return "\n".join([top] + body + [bottom])

    def spinner(text="Memuat...", duration=2.3):
        anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        end_time = time.time() + duration
        idx = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r{cyan}{text}{reset} {anim[idx % len(anim)]}")
            sys.stdout.flush()
            time.sleep(0.07)
            idx += 1
        sys.stdout.write("\r" + " " * (len(text) + 8) + "\r")

    # ========= KODE ASLI (TIDAK DIUBAH SEDIKITPUN) =========
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        print(box("DECOY MODE", ["Mode decoy aktif. Mengambil paket decoy..."], yellow))
        decoy = DecoyInstance.get_decoy("balance")
        
        decoy_package_detail = get_package(
            api_key,
            tokens,
            decoy["option_code"],
        )
        
        if not decoy_package_detail:
            print(box("FAILED", ["Failed to load decoy package details."], red))
            pause()
            return False
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        print(box("WARNING", [f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!"], yellow))
        balance_answer = input(f"{cyan}Apakah anda yakin ingin melanjutkan pembelian? (y/n): {reset}")
        if balance_answer.lower() != "y":
            print(box("CANCELLED", ["Pembelian dibatalkan oleh user."], red))
            pause()
            return None

    spinner("Mengambil data family...")
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print(box("FAILED", [f"Failed to get family data for code: {family_code}."], red))
        pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]

    print(box("FAMILY INFO", [
        f"Family: {family_name}",
        f"Total variant: {len(variants)}",
        f"Start from option: {start_from_option}"
    ], center=True))

    successful_purchases = []
    packages_count = 0
    for variant in variants:
        packages_count += len(variant["package_options"])
    
    purchase_count = 0
    start_buying = start_from_option <= 1

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            option_order = option["order"]
            if not start_buying and option_order == start_from_option:
                start_buying = True
            if not start_buying:
                print(box("SKIPPED", [f"Skipping option {option_order}. {option['name']}"], yellow))
                continue
            
            option_name = option["name"]
            option_price = option["price"]
            
            purchase_count += 1
            print(box("PROCESS", [f"Purchase {purchase_count} of {packages_count}"], yellow))
            print(box("", [f"Trying to buy: {variant_name} - {option_order}. {option_name} - Rp{option_price}"], white))
            spinner("Fetching package details", duration=2.0)

            payment_items = []
            
            try:
                if use_decoy:                
                    decoy = DecoyInstance.get_decoy("balance")
                    
                    decoy_package_detail = get_package(
                        api_key,
                        tokens,
                        decoy["option_code"],
                    )
                    
                    if not decoy_package_detail:
                        print(box("FAILED", ["Failed to load decoy package details."], red))
                        pause()
                        return False
                
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                print(box("ERROR", [
                    f"Exception occurred while fetching package details: {e}",
                    f"Failed to get package details for {variant_name} - {option_name}. Skipping."
                ], red))
                continue
            
            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )
            
            if use_decoy:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )
            
            res = None
            
            overwrite_amount = target_package_detail["package_option"]["price"]
            if use_decoy or overwrite_amount == 0:
                overwrite_amount += decoy_package_detail["package_option"]["price"]
                
            error_msg = ""

            try:
                print(box("SETTLEMENT", [
                    f"Mulai settlement pembayaran...",
                    f"Overwrite amount: Rp{overwrite_amount}"
                ], cyan))
                spinner("Processing settlement...", duration=3.0)

                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "🤑",
                    False,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=1
                )
                
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())
                        print(box("ADJUSTMENT", [f"Adjusted total amount to: {valid_amount}"], yellow))
                        spinner("Retrying settlement...", duration=2.0)

                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "SHARE_PACKAGE",
                            False,
                            overwrite_amount=valid_amount,
                            token_confirmation_idx=-1
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            error_msg = ""
                            successful_purchases.append(
                                f"{variant_name}|{option_order}. {option_name} - Rp{option_price}"
                            )
                            print(box("SUCCESS ✅", [f"Purchase {purchase_count} berhasil!"], green))
                            if pause_on_success: pause()
                        else:
                            error_msg = res.get("message", "")
                            print(box("FAILED ❌", [error_msg or "Settlement retry gagal."], red))
                else:
                    successful_purchases.append(
                        f"{variant_name}|{option_order}. {option_name} - Rp{option_price}"
                    )
                    print(box("SUCCESS ✅", [f"Purchase {purchase_count} berhasil!"], green))
                    if pause_on_success:
                        pause()

                # ✅ Tampilkan hasil JSON dengan format Code / Message / Status
                if res:
                    code_val = res.get("code", "-")
                    message_val = res.get("message", "-")
                    status_val = res.get("status", "-")
                    color_status = green if status_val == "SUCCESS" else red if status_val == "FAILED" else cyan

                    print(box("RESULT", [
                        f"{white}Code:{reset} {cyan}{code_val}{reset}",
                        f"{white}Message:{reset} {yellow}{message_val}{reset}",
                        f"{white}Status:{reset} {color_status}{status_val}{reset}"
                    ], white))
                else:
                    print(box("RESULT", ["Tidak ada hasil respon dari server."], yellow))
            except Exception as e:
                print(box("ERROR", [f"Exception occurred while creating order: {e}"], red))
                res = None

            print(box("STEP END", [f"Selesai purchase ke-{purchase_count}"], cyan))

            should_delay = error_msg == "" or "Failed call ipaas purchase" in error_msg
            if delay_seconds > 0 and should_delay:
                print(box("WAIT", [f"Menunggu {delay_seconds} detik sebelum next purchase..."], yellow))
                time.sleep(delay_seconds)
                
    print(box("SUMMARY", [
        f"Family: {family_name}",
        f"Successful: {len(successful_purchases)} dari {packages_count}"
    ], green, center=True))

    if len(successful_purchases) > 0:
        print(box("SUCCESSFUL PURCHASES", [
            f"- {p}" for p in successful_purchases
        ], cyan))

    pause()

def purchase_n_times(
    n: int,
    family_code: str,
    variant_code: str,
    option_order: int,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    import sys, time, shutil, re, json
    from random import randint

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m"
    )

    # 🧩 Utilitas tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(text, width): 
        import textwrap
        return textwrap.wrap(str(text), width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        pad_space = inner_width - visible_len(text)
        if pad_space < 0: pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 1)}{gray}│{reset}"

    def box(title="", lines=None, color=white, center=False):
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
        if lines:
            for line in lines:
                for wrapped in wrap_text(line, term_width - 10):
                    body.append(box_line(wrapped, color))
        return "\n".join([top] + body + [bottom])

    def spinner(text="Memuat...", duration=2.2):
        anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        end_time = time.time() + duration
        idx = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r{cyan}{text}{reset} {anim[idx % len(anim)]}")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1
        sys.stdout.write("\r" + " " * (len(text) + 8) + "\r")

    # ========= KODE ASLI (TIDAK DIUBAH SEDIKITPUN) =========
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        print(box("DECOY MODE", ["Mode decoy diaktifkan. Mengambil paket decoy..."], yellow))
        decoy = DecoyInstance.get_decoy("balance")
        
        decoy_package_detail = get_package(
            api_key,
            tokens,
            decoy["option_code"],
        )
        
        if not decoy_package_detail:
            print(box("FAILED", ["Failed to load decoy package details."], red))
            pause()
            return False
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        print(box("WARNING", [f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!"], yellow))
        balance_answer = input(f"{cyan}Apakah anda yakin ingin melanjutkan pembelian? (y/n): {reset}")
        if balance_answer.lower() != "y":
            print(box("CANCELLED", ["Pembelian dibatalkan oleh user."], red))
            pause()
            return None
    
    spinner("Fetching family data...")
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print(box("FAILED", [f"Failed to get family data for code: {family_code}."], red))
        pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = None
    for variant in variants:
        if variant["package_variant_code"] == variant_code:
            target_variant = variant
            break
    if not target_variant:
        print(box("FAILED", [f"Variant code {variant_code} not found in family {family_name}."], red))
        pause()
        return None

    target_option = None
    for option in target_variant["package_options"]:
        if option["order"] == option_order:
            target_option = option
            break
    if not target_option:
        print(box("FAILED", [f"Option order {option_order} not found in variant {target_variant['name']}."], red))
        pause()
        return None

    option_name = target_option["name"]
    option_price = target_option["price"]

    print(box("PURCHASE MODE", [
        f"Family: {family_name}",
        f"Variant: {target_variant['name']}",
        f"Option: {option_order}. {option_name} - Rp{option_price}",
        f"Total pembelian: {n}x"
    ], center=True))

    successful_purchases = []
    
    for i in range(n):
        print(box("PROCESS", [f"Purchase {i + 1} of {n} sedang diproses..."], yellow))
        print(box("", [f"Trying to buy: {target_variant['name']} - {option_order}. {option_name} - Rp{option_price}"], white))
        spinner("Fetching package details", duration=2.0)

        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    print(box("FAILED", ["Failed to load decoy package details."], red))
                    pause()
                    return False
            
            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None,
                None,
            )
        except Exception as e:
            print(box("ERROR", [
                f"Exception occurred while fetching package details: {e}",
                f"Failed to get package details for {target_variant['name']} - {option_name}. Skipping."
            ], red))
            continue
        
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        res = None
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            print(box("SETTLEMENT", [
                "Mengirim request settlement...",
                f"Total overwrite_amount: Rp{overwrite_amount}"
            ], cyan))
            spinner("Processing settlement...", duration=3.0)

            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(box("ADJUSTMENT", [f"Adjusted total amount to: {valid_amount}"], yellow))
                    spinner("Retrying settlement...", duration=2.0)
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{option_price}")
                        print(box("SUCCESS ✅", [f"Purchase {i + 1} berhasil!"], green))
                        if pause_on_success:
                            pause()
                    else:
                        print(box("FAILED ❌", ["Settlement retry gagal."], red))
            else:
                successful_purchases.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{option_price}")
                print(box("SUCCESS ✅", [f"Purchase {i + 1} berhasil!"], green))
                if pause_on_success:
                    pause()

            # ✅ Format hasil respon: Code / Message / Status
            if res:
                code_val = res.get("code", "-")
                message_val = res.get("message", "-")
                status_val = res.get("status", "-")
                color_status = green if status_val == "SUCCESS" else red if status_val == "FAILED" else cyan
                print(box("RESULT", [
                    f"{white}Code:{reset} {cyan}{code_val}{reset}",
                    f"{white}Message:{reset} {yellow}{message_val}{reset}",
                    f"{white}Status:{reset} {color_status}{status_val}{reset}"
                ], white))
            else:
                print(box("RESULT", ["Tidak ada hasil respon dari server."], yellow))
        except Exception as e:
            print(box("ERROR", [f"Exception occurred while creating order: {e}"], red))
            res = None

        print(box("STEP END", [f"Selesai purchase ke-{i + 1}"], cyan))

        if delay_seconds > 0 and i < n - 1:
            print(box("WAIT", [f"Menunggu {delay_seconds} detik sebelum pembelian berikutnya..."], yellow))
            time.sleep(delay_seconds)

    print(box("SUMMARY", [
        f"Total successful purchases: {len(successful_purchases)}/{n}",
        f"Family: {family_name}",
        f"Variant: {target_variant['name']}",
        f"Option: {option_order}. {option_name} - Rp{option_price}"
    ], green, center=True))
    
    if len(successful_purchases) > 0:
        print(box("SUCCESSFUL PURCHASES", [
            f"{idx + 1}. {purchase}" for idx, purchase in enumerate(successful_purchases)
        ], color=cyan))
    pause()
    return True

def purchase_n_times_by_option_code(
    n: int,
    option_code: str,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    import sys, time, shutil, re, json
    from random import randint

    # 🎨 Warna ANSI
    gray, reset, cyan, green, yellow, red, white, blue = (
        "\033[90m", "\033[0m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[97m", "\033[94m"
    )

    # 🔧 Utilitas Tampilan
    def visible_len(s): return len(re.sub(r'\x1b\[[0-9;]*m', '', s))
    def wrap_text(s, width): import textwrap; return textwrap.wrap(str(s), width=width)

    def box_line(text="", color=white):
        term_width = shutil.get_terminal_size((80, 20)).columns
        inner_width = term_width - 4
        pad_space = inner_width - visible_len(text)
        if pad_space < 0: pad_space = 0
        return f"{gray}│{reset} {color}{text}{reset}{' ' * (pad_space + 1)}{gray}│{reset}"

    def box(title="", lines=None, color=white, center=False):
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
        if lines:
            for line in lines:
                for wrapped in wrap_text(line, term_width - 10):
                    body.append(box_line(wrapped, color))
        return "\n".join([top] + body + [bottom])

    def spinner(text="Loading...", duration=2.2):
        anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        end_time = time.time() + duration
        idx = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r{cyan}{text}{reset} {anim[idx % len(anim)]}")
            sys.stdout.flush()
            time.sleep(0.07)
            idx += 1
        sys.stdout.write("\r" + " " * (len(text) + 8) + "\r")

    # ======== KODE ASLI (TIDAK DIUBAH SEDIKITPUN) ========
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        
        decoy_package_detail = get_package(
            api_key,
            tokens,
            decoy["option_code"],
        )
        
        if not decoy_package_detail:
            print(box("FAILED", ["Failed to load decoy package details."], red))
            pause()
            return False
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        print(box("WARNING", [
            f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!"
        ], yellow))
        balance_answer = input(f"{cyan}Apakah anda yakin ingin melanjutkan pembelian? (y/n): {reset}")
        if balance_answer.lower() != "y":
            print(box("CANCELLED", ["Pembelian dibatalkan oleh user."], red))
            pause()
            return None
    
    print(box("PURCHASE START", [f"Menjalankan {n}x pembelian paket..."], center=True))
    successful_purchases = []
    
    for i in range(n):
        print(box("PROCESS", [f"Purchase {i + 1} of {n} sedang diproses..."], yellow))
        spinner("Fetching package details")

        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                
                decoy_package_detail = get_package(
                    api_key,
                    tokens,
                    decoy["option_code"],
                )
                
                if not decoy_package_detail:
                    print(box("FAILED", ["Failed to load decoy package details."], red))
                    pause()
                    return False
            
            target_package_detail = get_package(
                api_key,
                tokens,
                option_code,
            )
        except Exception as e:
            print(box("ERROR", [f"Exception occurred while fetching package details: {e}"], red))
            continue
        
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        res = None
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            print(box("SETTLEMENT", [
                "Mengirim request pembayaran...",
                f"Total overwrite_amount: Rp{overwrite_amount}"
            ], cyan))
            spinner("Mengirim settlement request...", duration=3.0)

            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(box("ADJUSTMENT", [f"Adjusted total amount to: {valid_amount}"], yellow))
                    spinner("Mengulangi settlement...", duration=2.0)
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"Purchase {i + 1}")
                        print(box("SUCCESS ✅", [f"Purchase {i + 1} berhasil!"], green))
                        if pause_on_success:
                            pause()
                    else:
                        print(box("FAILED ❌", ["Settlement retry gagal."], red))
            else:
                successful_purchases.append(f"Purchase {i + 1}")
                print(box("SUCCESS ✅", [f"Purchase {i + 1} berhasil!"], green))
                if pause_on_success:
                    pause()

            # ✅ Tampilkan hasil JSON dalam bentuk Code / Message / Status
            if res:
                code_val = res.get("code", "-")
                message_val = res.get("message", "-")
                status_val = res.get("status", "-")

                color_status = (
                    green if status_val == "SUCCESS" else
                    red if status_val == "FAILED" else
                    cyan
                )

                print(box("RESULT", [
                    f"{white}Code:{reset} {cyan}{code_val}{reset}",
                    f"{white}Message:{reset} {yellow}{message_val}{reset}",
                    f"{white}Status:{reset} {color_status}{status_val}{reset}"
                ], color=white))
            else:
                print(box("RESULT", ["Tidak ada hasil respon dari server."], yellow))
        except Exception as e:
            print(box("ERROR", [f"Exception occurred while creating order: {e}"], red))
            res = None

        print(box("STEP END", [f"Selesai purchase ke-{i + 1}"], cyan))
        print(gray + "─" * shutil.get_terminal_size((80, 20)).columns + reset)

        if delay_seconds > 0 and i < n - 1:
            print(box("WAIT", [f"Menunggu {delay_seconds} detik sebelum pembelian berikutnya..."], yellow))
            time.sleep(delay_seconds)

    # 🧾 Ringkasan akhir
    print(box("SUMMARY", [
        f"Total successful purchases: {len(successful_purchases)}/{n}"
    ], center=True, color=green))
    if len(successful_purchases) > 0:
        print(box("SUCCESSFUL PURCHASES", [
            f"{idx + 1}. {purchase}" for idx, purchase in enumerate(successful_purchases)
        ], color=cyan))
    pause()
    return True