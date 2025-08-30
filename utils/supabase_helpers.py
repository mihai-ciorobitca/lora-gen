from extensions import supabase, supabase_admin


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


def add_pending_job(user_email, prompt, filename, prompt_id):
    supabase.table("jobs").insert(
        {
            "email": user_email,
            "prompt": prompt,
            "filename": filename,
            "status": False,
            "id": prompt_id,
        }
    ).execute()


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
    supabase.table("jobs").update({"status": True, "url": url}).eq(
        "email", user_email
    ).eq("filename", filename).execute()
