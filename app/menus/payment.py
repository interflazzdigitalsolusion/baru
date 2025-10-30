from datetime import datetime, timedelta
from app.client.engsel2 import get_pending_transaction, get_transaction_history
from app.menus.util import clear_screen

def show_transaction_history(api_key, tokens):
    import sys, time, shutil, re, textwrap

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
            sys.stdout.flush(); time.sleep(0.07)
        sys.stdout.write("\r" + " " * (len(text) + 5) + "\r")

    def bordered_input(prompt_text):
        term_width = shutil.get_terminal_size((80, 20)).columns
        top = f"{gray}┌{'─' * (term_width - 2)}┐{reset}"
        left = f"{gray}│{reset} {cyan}{prompt_text}{reset} "
        sys.stdout.write(top + "\n" + left)
        user_input = input()
        return user_input.strip()

    # ========== KODE ASLI MULAI (TIDAK DIUBAH SEDIKITPUN) ==========
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        print(box("RIWAYAT TRANSAKSI", [], center=True))
        spinner("Mengambil data riwayat transaksi...")

        data = None
        history = []
        try:
            data = get_transaction_history(api_key, tokens)
            history = data.get("list", [])
        except Exception as e:
            print(box("FAILED", [f"Gagal mengambil riwayat transaksi: {e}"], red))
            history = []
        
        if len(history) == 0:
            print(box("INFO", ["Tidak ada riwayat transaksi."], yellow))
        else:
            for idx, transaction in enumerate(history, start=1):
                transaction_timestamp = transaction.get("timestamp", 0)
                dt = datetime.fromtimestamp(transaction_timestamp)
                dt_jakarta = dt - timedelta(hours=7)
                formatted_time = dt_jakarta.strftime("%d %B %Y | %H:%M WIB")

                lines = [
                    f"{red}Judul{reset}: {yellow}{transaction['title']}{reset}",
                    f"{red}Harga{reset}: {green}{transaction['price']}{reset}",
                    f"{red}Tanggal{reset}: {cyan}{formatted_time}{reset}",
                    f"{red}Metode Pembayaran{reset}: {yellow}{transaction['payment_method_label']}{reset}",
                    f"{red}Status Transaksi{reset}: {green}{transaction['status']}{reset}",
                    f"{red}Status Pembayaran{reset}: {green}{transaction['payment_status']}{reset}",
                ]
                print(box(f"{idx}. TRANSAKSI", lines))

        # Opsi menu
        print(box("MENU", [
            f"{cyan}0.{reset} Refresh",
            f"{green}00.{reset} Kembali ke Menu Utama"
        ]))

        choice = bordered_input("Pilih opsi:")
        if choice == "0":
            continue
        elif choice == "00":
            in_transaction_menu = False
        else:
            print(box("INVALID", ["Opsi tidak valid. Silakan coba lagi."], red))