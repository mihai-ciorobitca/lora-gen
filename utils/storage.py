from extensions import supabase

def upload_to_bucket(bucket: str, path: str, content: bytes) -> str:
    try:
        supabase.storage.from_(bucket).upload(
            path, content, {"content-type": "image/png"}
        )
    except Exception:
        supabase.storage.from_(bucket).update(
            path, content, {"content-type": "image/png"}
        )

    return supabase.storage.from_(bucket).get_public_url(path)
