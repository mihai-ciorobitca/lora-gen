from extensions import supabase_admin

def upload_to_bucket(bucket: str, path: str, content: bytes) -> str:
    try:
        supabase_admin.storage.from_(bucket).upload(
            path, content, {"content-type": "image/png"}
        )
    except Exception:
        supabase_admin.storage.from_(bucket).update(
            path, content, {"content-type": "image/png"}
        )

    return supabase_admin.storage.from_(bucket).get_public_url(path)
