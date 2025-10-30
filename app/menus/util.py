import app.menus.banner as banner
ascii_art = banner.load("https://me.mashu.lol/mebanner880.png", globals())

from html.parser import HTMLParser
import os
import re
import textwrap
import platform
import shutil
from itertools import cycle

# Tambahan flag untuk menyembunyikan banner tanpa menghapus kode
HIDE_BANNER = True  # ubah ke False kalau mau banner ditampilkan lagi

# Fungsi untuk menghitung panjang teks tanpa kode warna ANSI
def visible_len(s):
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

def center_ansi_text(text, width):
    """Center text that contains ANSI colors"""
    pad_total = width - visible_len(text)
    pad_left = pad_total // 2 if pad_total > 0 else 0
    pad_right = pad_total - pad_left if pad_total > 0 else 0
    return " " * pad_left + text + " " * pad_right

def clear_screen():
    print("Clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')

    if not HIDE_BANNER:
        if ascii_art:
            ascii_art.to_terminal(columns=55)
    else:
        # --- STYLE CENTER + BORDER RAPAT & RAPIH ---
        reset = "\033[0m"
        bold = "\033[1m"
        cyan = "\033[96m"
        white = "\033[97m"
        gray = "\033[90m"
        yellow = "\033[93m"
        blue = "\033[94m"
        magenta = "\033[95m"
        green = "\033[92m"
        colors = [
            "\033[91m", "\033[93m", "\033[92m",
            "\033[96m", "\033[94m", "\033[95m"
        ]
        color_cycle = cycle(colors)
        term_width = shutil.get_terminal_size((80, 20)).columns

        # === Judul: OPENAPI.BIZ.ID (center stabil) ===
        title = " MINYAK ENGSEL "
        colored_title = "".join(
            bold + next(color_cycle) + ch if ch.strip() else ch
            for ch in title
        )
        title_centered = center_ansi_text(colored_title, term_width - 2)

        # Top border
        print(gray + "┌" + "─" * (term_width - 2) + "┐" + reset)
        print(gray + "│" + reset + title_centered + gray + "│" + reset)
        print(gray + "└" + "─" * (term_width - 2) + "┘" + reset)

        # === DEVICE INFO BOX ===
        system = platform.system()
        release = platform.release()
        python_ver = platform.python_version()
        node = platform.node()
        arch = platform.machine()

        info_title = f"{white}{bold}DEVICE INFORMATION{reset}"
        print(gray + "┌" + "─" * (term_width - 2) + "┐" + reset)
        print(gray + "│" + reset + center_ansi_text(info_title, term_width - 2) + gray + "│" + reset)
        print(gray + "├" + "─" * (term_width - 2) + "┤" + reset)

        info_lines = [
            f"{bold}{yellow}System{reset} : {cyan}{system} {release}{reset}",
            f"{bold}{yellow}Device{reset} : {green}{node}{reset}",
            f"{bold}{yellow}Python{reset} : {magenta}{python_ver}{reset}",
            f"{bold}{yellow}Arch{reset}   : {blue}{arch}{reset}"
        ]

        # setiap baris info dibuat agar panjang total = term_width
        for line in info_lines:
            line_visible = visible_len(line)
            pad = (term_width - 4) - line_visible
            print(gray + "│ " + reset + line + " " * pad + gray + " │" + reset)

        print(gray + "└" + "─" * (term_width - 2) + "┘" + reset)
        print()

    # --- KODE ASLI TETAP UTUH ---
    # if user_info:
    #     credit = user_info.get("credit", 0)
    #     premium_credit = user_info.get("premium_credit", 0)
    #     width = 55 
    #     print("=" * width)
    #     print(f" Credit: {credit} | Premium Credit: {premium_credit} ".center(width))
    #     print("=" * width)
    #     print("")

def pause():
    input("\nPress enter to continue...")

class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))

def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()

def format_quota_byte(quota_byte: int) -> str:
    GB = 1024 ** 3
    MB = 1024 ** 2
    KB = 1024
    if quota_byte >= GB:
        return f"{quota_byte / GB:.2f} GB"
    elif quota_byte >= MB:
        return f"{quota_byte / MB:.2f} MB"
    elif quota_byte >= KB:
        return f"{quota_byte / KB:.2f} KB"
    else:
        return f"{quota_byte} B"
