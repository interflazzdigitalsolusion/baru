from datetime import datetime  
import json  
from app.menus.util import pause, clear_screen, format_quota_byte  
from app.client.engsel3 import (  
    get_group_data, get_group_members, validate_circle_member,  
    invite_circle_member, remove_circle_member, accept_circle_invitation  
)  
from app.service.auth import AuthInstance  
from app.client.encrypt import decrypt_circle_msisdn  
  
WIDTH = 55  
  
def show_circle_info(api_key: str, tokens: dict):  
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
    in_circle_menu = True  
    user: dict = AuthInstance.get_active_user()  
    my_msisdn = user.get("number", "")  
  
    while in_circle_menu:  
        clear_screen()  
        spinner("Mengambil data Circle...")  
        group_res = get_group_data(api_key, tokens)  
        if group_res.get("status") != "SUCCESS":  
            print(box("FAILED", ["Failed to fetch circle data."], red))  
            pause()  
            return  
          
        group_data = group_res.get("data", {})          
        group_id = group_data.get("group_id", "")  
  
        if group_id == "":  
            print(box("INFO", ["You are not part of any Circle."], yellow))  
            pause()  
            return  
          
        group_status = group_data.get("group_status", "N/A")  
        if group_status == "BLOCKED":  
            print(box("BLOCKED", ["This Circle is currently blocked."], red))  
            pause()  
            return  
          
        group_name = group_data.get("group_name", "N/A")  
        owner_name = group_data.get("owner_name", "N/A")  
          
        spinner("Mengambil data anggota...")  
        members_res = get_group_members(api_key, tokens, group_id)  
        if members_res.get("status") != "SUCCESS":  
            print(box("FAILED", ["Failed to fetch circle members."], red))  
            pause()  
            return  
          
        members_data = members_res.get("data", {})  
        members = members_data.get("members", [])  
        if len(members) == 0:  
            print(box("INFO", ["No members found in the Circle."], yellow))  
            pause()  
            return  
          
        parent_member_id = ""  
        parent_subs_id = ""  
        parrent_msisdn = ""  
        for member in members:  
            if member.get("member_role", "") == "PARENT":  
                parent_member_id = member.get("member_id", "")  
                parent_subs_id = member.get("subscriber_number", "")  
                parrent_msisdn_encrypted = member.get("msisdn", "")  
                parrent_msisdn = decrypt_circle_msisdn(api_key, parrent_msisdn_encrypted)  
          
        package = members_data.get("package", {})  
        package_name = package.get("name", "N/A")  
        benefit = package.get("benefit", {})  
        allocation_byte = benefit.get("allocation", 0)  
        consumption_byte = benefit.get("consumption", 0)  
        remaining_byte = benefit.get("remaining", 0)  
          
        formatted_allocation = format_quota_byte(allocation_byte)  
        formatted_consumption = format_quota_byte(consumption_byte)  
        formatted_remaining = format_quota_byte(remaining_byte)  
                  
        clear_screen()  

        # 🌐 HEADER TAMBAHAN (CENTER BORDER)
        term_width = shutil.get_terminal_size((80, 20)).columns
        print(f"{gray}┌{'─' * (term_width - 2)}┐{reset}")
        title = "CIRCLE INFORMATION"
        pad_total = term_width - 2 - len(title)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        print(f"{gray}│{reset}{' ' * pad_left}{cyan}{title}{reset}{' ' * pad_right}{gray}│{reset}")
        print(f"{gray}└{'─' * (term_width - 2)}┘{reset}\n")

        # 📦 Info Circle Header  
        header_lines = [  
            f"{cyan}Circle{reset}: {green}{group_name}{reset} ({group_status})",  
            f"{cyan}Owner{reset}: {yellow}{owner_name}{reset} {parrent_msisdn}",  
            f"{cyan}Package{reset}: {green}{package_name}{reset}",  
            f"{cyan}Usage{reset}: {yellow}{formatted_remaining}{reset} / {green}{formatted_allocation}{reset}",  
        ]  
        print(box("", header_lines, white))  
  
        # 👥 Daftar Anggota  
        print(box("MEMBERS", [f"Total Members: {len(members)}"], center=False))  
        for idx, member in enumerate(members, start=1):  
            encrypted_msisdn = member.get("msisdn", "")  
            msisdn = decrypt_circle_msisdn(api_key, encrypted_msisdn)  
            member_role = member.get("member_role", "N/A")  
            member_name = member.get("member_name", "N/A")  
            slot_type = member.get("slot_type", "N/A")  
            member_status = member.get("status", "N/A")  
            join_date_ts = member.get("join_date", 0)  
            join_date = datetime.fromtimestamp(join_date_ts).strftime("%Y-%m-%d") if join_date_ts else "N/A"  
  
            me_mark = "(You)" if str(msisdn) == str(my_msisdn) else ""  
            formated_quota_allocated = format_quota_byte(member.get("allocation", 0))  
            formated_quota_used = format_quota_byte(member.get("allocation", 0) - member.get("remaining", 0))  
  
            lines = [  
                f"{green}{idx}.{reset} {yellow}{msisdn or '<No Number>'}{reset} ({member_name}) {cyan}{me_mark}{reset}",  
                f"Role: {member_role} | Slot: {slot_type} | Status: {member_status}",  
                f"Joined: {join_date}",  
                f"Usage: {formated_quota_used} / {formated_quota_allocated}"  
            ]  
            print(box("", lines, white))  
  
        # ⚙️ Menu Opsi  
        menu_lines = [  
            f"{cyan}1.{reset} Invite Member to Circle",  
            f"{cyan}del <number>{reset} - Remove Member (e.g., del 2)",  
            f"{cyan}acc <number>{reset} - Accept Invitation / Force Accept",  
            f"{green}00.{reset} Kembali ke menu utama"  
        ]  
        print(box("OPTIONS", menu_lines, color=white))  
  
        choice = bordered_input("Pilih opsi:")  
        if choice == "00":  
            in_circle_menu = False  
  
        elif choice == "1":  
            msisdn_to_invite = bordered_input("Enter member MSISDN (62...):")  
            validate_res = validate_circle_member(api_key, tokens, msisdn_to_invite)  
            if validate_res.get("status") == "SUCCESS":  
                if validate_res.get("data", {}).get("response_code", "") != "200-2001":  
                    print(box("ERROR", [f"Cannot invite {msisdn_to_invite}: {validate_res.get('data', {}).get('message', 'Unknown error')}"], red))  
                    pause()  
                    continue  
              
            member_name = bordered_input("Enter member name:")  
            invite_res = invite_circle_member(api_key, tokens, msisdn_to_invite, member_name, group_id, parent_member_id)  
            if invite_res.get("status") == "SUCCESS":  
                if invite_res.get("data", {}).get("response_code", "") == "200-00":  
                    print(box("SUCCESS", [f"Invitation sent to {msisdn_to_invite} successfully."], green))  
                else:  
                    print(box("FAILED", [f"Failed to invite {msisdn_to_invite}: {invite_res.get('data', {}).get('message', 'Unknown error')}"], red))  
            pause()  
  
        elif choice.startswith("del "):  
            try:  
                member_number = int(choice.split(" ")[1])  
                if member_number < 1 or member_number > len(members):  
                    print(box("INVALID", ["Invalid member number."], red))  
                    pause(); continue  
                member_to_remove = members[member_number - 1]  
                if member_to_remove.get("member_role", "") == "PARENT":  
                    print(box("ERROR", ["Cannot remove parent from Circle."], yellow))  
                    pause(); continue  
  
                is_last_member = len(members) == 2  
                if is_last_member:  
                    print(box("ERROR", ["Cannot remove last member from Circle."], yellow))  
                    pause(); continue  
  
                msisdn_to_remove = decrypt_circle_msisdn(api_key, member_to_remove.get("msisdn", ""))  
                confirm = bordered_input(f"Remove {msisdn_to_remove}? (y/n):").lower()  
                if confirm != "y":  
                    print(box("CANCELLED", ["Removal cancelled."], yellow))  
                    pause(); continue  
  
                remove_res = remove_circle_member(api_key, tokens, member_to_remove.get("member_id", ""), group_id, parent_member_id, is_last_member)  
                if remove_res.get("status") == "SUCCESS":  
                    print(box("SUCCESS", [f"{msisdn_to_remove} removed from Circle."], green))  
                    print(json.dumps(remove_res, indent=2))  
                else:  
                    print(box("FAILED", [f"Error: {remove_res}"], red))  
            except ValueError:  
                print(box("INVALID", ["Invalid input format for deletion."], red))  
            pause()  
  
        elif choice.startswith("acc "):  
            try:  
                member_number = int(choice.split(" ")[1])  
                if member_number < 1 or member_number > len(members):  
                    print(box("INVALID", ["Invalid member number."], red))  
                    pause(); continue  
                member_to_accept = members[member_number - 1]  
                if member_to_accept.get("status", "") != "INVITED":  
                    print(box("INFO", ["This member is not in invited state."], yellow))  
                    pause(); continue  
  
                msisdn_to_accept = decrypt_circle_msisdn(api_key, member_to_accept.get("msisdn", ""))  
                confirm = bordered_input(f"Accept invitation for {msisdn_to_accept}? (y/n):").lower()  
                if confirm != "y":  
                    print(box("CANCELLED", ["Acceptance cancelled."], yellow))  
                    pause(); continue  
  
                accept_res = accept_circle_invitation(api_key, tokens, group_id, member_to_accept.get("member_id", ""))  
                if accept_res.get("status") == "SUCCESS":  
                    print(box("SUCCESS", [f"Invitation for {msisdn_to_accept} accepted."], green))  
                    print(json.dumps(accept_res, indent=2))  
                else:  
                    print(box("FAILED", [f"Error: {accept_res}"], red))  
            except ValueError:  
                print(box("INVALID", ["Invalid input format for acceptance."], red))  
            pause()