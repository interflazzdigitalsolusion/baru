import json  
from app.client.engsel import send_api_request  
from app.menus.util import format_quota_byte  
import sys, time  

# 🔄 Loader animasi reusable
def spinner(text="Loading..."):
    anim = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(18):
        sys.stdout.write(f"\r{text} {anim[i % len(anim)]}")
        sys.stdout.flush()
        time.sleep(0.07)
    sys.stdout.write("\r" + " " * (len(text) + 8) + "\r")


def get_pending_transaction(api_key: str, tokens: dict) -> dict:  
    path = "api/v8/profile"  

    raw_payload = {  
        "is_enterprise": False,  
        "lang": "en"  
    }  

    spinner("Fetching pending transactions...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    return res.get("data")  


def get_transaction_history(api_key: str, tokens: dict) -> dict:  
    path = "payments/api/v8/transaction-history"  

    raw_payload = {  
        "is_enterprise": False,  
        "lang": "en"  
    }  

    spinner("Fetching transaction history...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    # print(json.dumps(res, indent=4))  
    return res.get("data")  


def get_tiering_info(api_key: str, tokens: dict) -> dict:  
    path = "gamification/api/v8/loyalties/tiering/info"  

    raw_payload = {  
        "is_enterprise": False,  
        "lang": "en"  
    }  

    spinner("Fetching tiering info...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    # print(json.dumps(res, indent=4))  
      
    if res:  
        return res.get("data", {})  
    return {}  


def unsubscribe(  
    api_key: str,  
    tokens: dict,  
    quota_code: str,  
    product_domain: str,  
    product_subscription_type: str,  
) -> bool:  
    path = "api/v8/packages/unsubscribe"  

    raw_payload = {  
        "product_subscription_type": product_subscription_type,  
        "quota_code": quota_code,  
        "product_domain": product_domain,  
        "is_enterprise": False,  
        "unsubscribe_reason_code": "",  
        "lang": "en",  
        "family_member_id": ""  
    }  
      
    # print(f"Payload: {json.dumps(raw_payload, indent=4)}")  

    try:  
        spinner(f"Unsubscribing {quota_code}...")
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
        print(json.dumps(res, indent=4))  

        if res and res.get("code") == "000":  
            return True  
        else:  
            return False  
    except Exception as e:  
        return False  


def get_family_data(  
    api_key: str,  
    tokens: dict,  
) -> dict:  
    path = "sharings/api/v8/family-plan/member-info"  

    raw_payload = {  
        "group_id": 0,  
        "is_enterprise": False,  
        "lang": "en"  
    }  

    spinner("Fetching family data...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    return res  


def validate_msisdn(  
    api_key: str,  
    tokens: dict,  
    msisdn: str,  
) -> dict:  
    path = "api/v8/auth/validate-msisdn"  

    raw_payload = {  
        "with_bizon": False,  
        "with_family_plan": True,  
        "is_enterprise": False,  
        "with_optimus": False,  
        "lang": "en",  
        "msisdn": msisdn,  
        "with_regist_status": False,  
        "with_enterprise": False  
    }  

    spinner(f"Validating msisdn {msisdn}...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    return res  


def change_member(  
    api_key: str,  
    tokens: dict,  
    parent_alias: str,  
    alias: str,  
    slot_id: int,  
    family_member_id: str,  
    new_msisdn: str,  
) -> dict:  
    path = "sharings/api/v8/family-plan/change-member"  

    raw_payload = {  
        "parent_alias": parent_alias,  
        "is_enterprise": False,  
        "slot_id": slot_id,  
        "alias": alias,  
        "lang": "en",  
        "msisdn": new_msisdn,  
        "family_member_id": family_member_id  
    }  
      
    spinner(f"Assigning slot {slot_id} to {new_msisdn}...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    return res  


def remove_member(  
    api_key: str,  
    tokens: dict,  
    family_member_id: str,  
) -> dict:  
    path = "sharings/api/v8/family-plan/remove-member"  

    raw_payload = {  
        "is_enterprise": False,  
        "family_member_id": family_member_id,  
        "lang": "en"  
    }  

    spinner(f"Removing family member {family_member_id}...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    return res  


def set_quota_limit(  
    api_key: str,  
    tokens: dict,  
    original_allocation: int,  
    new_allocation: int,  
    family_member_id: str,  
) -> dict:  
    path = "sharings/api/v8/family-plan/allocate-quota"  

    raw_payload = {  
        "is_enterprise": False,  
        "member_allocations": [{  
            "new_text_allocation": 0,  
            "original_text_allocation": 0,  
            "original_voice_allocation": 0,  
            "original_allocation": original_allocation,  
            "new_voice_allocation": 0,  
            "message": "",  
            "new_allocation": new_allocation,  
            "family_member_id": family_member_id,  
            "status": ""  
        }],  
        "lang": "en"  
    }  
      
    formatted_new_allocation = format_quota_byte(new_allocation)  

    spinner(f"Setting quota limit for family member {family_member_id} to {formatted_new_allocation} MB...")
    res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")  
    return res