from datetime import datetime
import json
from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.engsel2 import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn

WIDTH = 55

def show_family_info(api_key: str, tokens: dict):
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

    # =====================================================
    # 🧱 KODE ASLI DIMULAI (TIDAK DIUBAH SEDIKITPUN)
    # =====================================================
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        spinner("Mengambil data Family Plan...")
        res = get_family_data(api_key, tokens)
        if not res.get("data"):
            print(box("FAILED", ["Failed to get family data."], red))
            pause()
            return
        
        family_detail = res["data"]
        plan_type = family_detail["member_info"]["plan_type"]
        
        if plan_type == "":
            print(box("INFO", ["You are not family plan organizer."], yellow))
            pause()
            return
        
        parent_msisdn = family_detail["member_info"]["parent_msisdn"]
        members = family_detail["member_info"]["members"]
        empyt_slots = [slot for slot in members if slot.get("msisdn") == ""]
        
        total_quota_byte = family_detail["member_info"].get("total_quota", 0)
        remaining_quota_byte = family_detail["member_info"].get("remaining_quota", 0)
        
        total_quota_human = format_quota_byte(total_quota_byte)
        remaining_quota_human = format_quota_byte(remaining_quota_byte)
        
        end_date_ts = family_detail["member_info"].get("end_date", 0)
        end_date = datetime.fromtimestamp(end_date_ts).strftime("%Y-%m-%d")

        # Header Family Info
        clear_screen()
        header_lines = [
            f"{red}Plan{reset}: {cyan}{plan_type}{reset}",
            f"{red}Parent{reset}: {yellow}{parent_msisdn}{reset}",
            f"{red}Shared Quota{reset}: {green}{remaining_quota_human}{reset} / {yellow}{total_quota_human}{reset}",
            f"{red}Expired{reset}: {cyan}{end_date}{reset}"
        ]
        print(box("FAMILY PLAN INFO", header_lines, color=white))

        # Member list
        member_lines = [f"Members aktif: {len(members) - len(empyt_slots)}/{len(members)}"]
        print(box("DAFTAR MEMBER", member_lines, center=False))

        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "N/A")
            alias = member.get("alias", "N/A")
            member_type = member.get("member_type", "N/A")
            add_chances = member.get("add_chances", 0)
            total_add_chances = member.get("total_add_chances", 0)
            quota_allocated = format_quota_byte(member.get("usage", {}).get("quota_allocated", 0))
            quota_used = format_quota_byte(member.get("usage", {}).get("quota_used", 0))
            msisdn_display = f"{yellow}{msisdn}{reset}" if msisdn else f"{red}<Empty Slot>{reset}"

            lines = [
                f"{green}{idx}.{reset} {msisdn_display} ({alias}) | {cyan}{member_type}{reset}",
                f"Add Chances: {add_chances}/{total_add_chances}",
                f"Usage: {quota_used} / {quota_allocated}"
            ]
            print(box("", lines))

        # Options
        print(box("OPTIONS", [
            f"{cyan}1.{reset} Change Member",
            f"{cyan}limit <slot> <MB>{reset}  Set Quota Limit",
            f"{cyan}del <slot>{reset}         Remove Member",
            f"{green}00.{reset} Back to Main Menu"
        ]))

        choice = bordered_input("Enter your choice:")
        if choice == "1":
            slot_idx = bordered_input("Enter slot number:")
            target_msisdn = bordered_input("Enter new member phone (62..):")
            parent_alias = bordered_input("Enter your alias:")
            child_alias = bordered_input("Enter new member alias:")

            try:
                slot_idx_int = int(slot_idx)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print(box("INVALID", ["Invalid slot number."], red))
                    pause(); return
                if members[slot_idx_int - 1].get("msisdn") != "":
                    print(box("ERROR", ["Selected slot is not empty."], yellow))
                    pause(); return

                family_member_id = members[slot_idx_int - 1]["family_member_id"]
                slot_id = members[slot_idx_int - 1]["slot_id"]

                validation_res = validate_msisdn(api_key, tokens, target_msisdn)
                if validation_res.get("status") != "SUCCESS":
                    print(box("FAILED", [f"MSISDN validation failed: {validation_res.get('message', 'Unknown error')}"], red))
                    pause(); return
                print(box("SUCCESS", ["MSISDN validation successful."], green))

                target_role = validation_res["data"].get("family_plan_role", "")
                if target_role != "NO_ROLE":
                    print(box("ERROR", [f"{target_msisdn} already part of another family plan ({target_role})."], yellow))
                    pause(); return

                confirm = bordered_input(f"Assign {target_msisdn} to slot {slot_idx_int}? (y/n):").lower()
                if confirm != "y":
                    print(box("CANCELLED", ["Operation cancelled by user."], yellow))
                    pause(); return

                change_member_res = change_member(api_key, tokens, parent_alias, child_alias, slot_id, family_member_id, target_msisdn)
                if change_member_res.get("status") == "SUCCESS":
                    print(box("SUCCESS", ["Member changed successfully."], green))
                else:
                    print(box("FAILED", [f"{change_member_res.get('message', 'Unknown error')}"], red))
                print(json.dumps(change_member_res, indent=4))
            except ValueError:
                print(box("INVALID", ["Invalid slot number."], red))
            pause()

        elif choice.startswith("del "):
            _, slot_num = choice.split(" ", 1)
            try:
                slot_idx_int = int(slot_num)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print(box("INVALID", ["Invalid slot number."], red))
                    pause(); return
                member = members[slot_idx_int - 1]
                if member.get("msisdn") == "":
                    print(box("INFO", ["Selected slot is already empty."], yellow))
                    pause(); return

                confirm = bordered_input(f"Remove member {member.get('msisdn')} from slot {slot_idx_int}? (y/n):").lower()
                if confirm != "y":
                    print(box("CANCELLED", ["Operation cancelled by user."], yellow))
                    pause(); return

                family_member_id = member["family_member_id"]
                res = remove_member(api_key, tokens, family_member_id)
                if res.get("status") == "SUCCESS":
                    print(box("SUCCESS", ["Member removed successfully."], green))
                else:
                    print(box("FAILED", [f"{res.get('message', 'Unknown error')}"], red))
                print(json.dumps(res, indent=4))
            except ValueError:
                print(box("INVALID", ["Invalid slot number."], red))
            pause()

        elif choice.startswith("limit "):
            _, slot_num, new_quota_mb = choice.split(" ", 2)
            try:
                slot_idx_int = int(slot_num)
                new_quota_mb_int = int(new_quota_mb)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print(box("INVALID", ["Invalid slot number."], red))
                    pause(); return

                member = members[slot_idx_int - 1]
                if member.get("msisdn") == "":
                    print(box("ERROR", ["Selected slot is empty. Cannot set limit."], yellow))
                    pause(); return

                family_member_id = member["family_member_id"]
                original_allocation = member.get("usage", {}).get("quota_allocated", 0)
                new_allocation_byte = new_quota_mb_int * 1024 * 1024

                res = set_quota_limit(api_key, tokens, original_allocation, new_allocation_byte, family_member_id)
                if res.get("status") == "SUCCESS":
                    print(box("SUCCESS", ["Quota limit set successfully."], green))
                else:
                    print(box("FAILED", [f"{res.get('message', 'Unknown error')}"], red))
                print(json.dumps(res, indent=4))
            except ValueError:
                print(box("INVALID", ["Invalid input."], red))
            pause()

        elif choice == "00":
            in_family_menu = False
            return