from extensions import supabase, supabase_admin
import requests
import time
import os

CRON_JOBS_API_KEY = os.getenv("CRON_JOBS_API_KEY")

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


import time, requests, json

def schedule_check(user_email, filename):
    run_time = int(time.time()) + 40

    url = "https://api.cron-job.org/jobs"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CRON_JOBS_API_KEY}",
    }

    payload = {
        "job": {
            "url": "https://lora-gen.vercel.app/api/check_job",
            "enabled": True,
            "saveResponses": True,
            "httpMethod": "POST", 
            "body": json.dumps({"email": user_email, "filename": filename}),
            "headers": [
                {"name": "Content-Type", "value": "application/json"}
            ],
            "schedule": {
                "timezone": "Europe/Berlin",
                "expiresAt": 0,
                "runTime": run_time
            }
        }
    }

    r = requests.put(url, headers=headers, json=payload)
    print(r.status_code, r.text)


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
