from extensions import supabase, supabase_admin
import requests
import time
import json
import os

def user_exists(email: str) -> bool:
    res = supabase_admin.auth.admin.list_users()
    return any(
        user.user_metadata and user.user_metadata.get("email") == email for user in res
    )


def return_user(email: str):
    res = supabase_admin.auth.admin.list_users()
    for user in res:
        if user.user_metadata and user.user_metadata.get("email") == email:
            return user
    return None


def schedule_check(user_email, filename):
    print("Scheduling Zeplo job check for", user_email, filename, flush=True)

    ZEPLO_TOKEN = os.getenv("ZEPLO_TOKEN")
    if not ZEPLO_TOKEN:
        print("❌ ERROR: ZEPLO_TOKEN not set in env", flush=True)
        return

    url = f"https://zeplo.to/https://lora-gen.vercel.app/api/check_job?_delay=40s&_retry=3&_token={ZEPLO_TOKEN}"

    payload = {"email": user_email, "filename": filename}
    headers = {"Content-Type": "application/json"}

    r = requests.post(url, headers=headers, data=json.dumps(payload))
    print("Status:", r.status_code, flush=True)
    try:
        print("Response JSON:", r.json(), flush=True)
    except Exception:
        print("Response Text:", r.text, flush=True)




def add_pending_job(user_email, prompt, filename, prompt_id):
    supabase.table("jobs").insert(
        {
            "email": user_email,
            "prompt": prompt,
            "filename": filename,
            "prompt_id": prompt_id,
        }
    ).execute()
    schedule_check(user_email, filename)



def get_pending_jobs(user_email):
    res = (
        supabase.table("jobs")
        .select("*")
        .eq("email", user_email)
        .eq("status", False)
        .execute()
    )
    return res.data or []


def get_all_pending_jobs():
    res = supabase.table("jobs").select("*").eq("status", False).execute()
    return res.data or []


def get_history(user_email):
    res = (
        supabase.table("jobs")
        .select("*")
        .eq("email", user_email)
        .eq("status", True)
        .order("created_at", desc=True)
        .execute()
    )
    print("History fetch result:", res)
    return res.data or []


def mark_job_complete(user_email, filename, url):
    supabase_admin.table("jobs").update({"status": True, "url": url}).eq(
        "email", user_email
    ).eq("filename", filename).execute()
