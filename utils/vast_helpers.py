import httpx, time, traceback
from flask import session
from extensions import API_KEY, logger
from extensions import logger
from utils.storage import upload_to_bucket

def get_instance_info(instance_id: str | int) -> dict:
    if not API_KEY:
        raise RuntimeError("Server misconfigured: API_KEY missing")

    if "instance" in session:
        inst = session["instance"]
        if inst["expires_at"] > time.time():
            return inst

    url = f"https://console.vast.ai/api/v0/instances/{instance_id}/"

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Authorization": f"Bearer {API_KEY}",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("Error fetching Vast.ai instance info: %s", e)
        raise RuntimeError("Failed to fetch instance info")

    try:
        inst = data["instances"]
        token = inst["jupyter_token"]
        ip = inst["public_ipaddr"]
        port = int(inst["direct_port_end"])

        session["instance"] = {
            "token": token,
            "ip_address": ip,
            "port": port,
            "expires_at": time.time() + 3600,
        }
        return session["instance"]

    except Exception as e:
        logger.error("Invalid Vast.ai payload: %s; data=%s", e, data)
        raise RuntimeError("Vast.ai response missing fields")

def view_request(username: str, filename: str, cookies: dict, base_url: str, bucket: str = "generated") -> str:
    payload = {"filename": f"{filename}_00001_.png", "type": "output", "subfolder": username}

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(f"{base_url}/view", params=payload, cookies=cookies, headers=headers)
            resp.raise_for_status()
            content = resp.content
            print(content)
    except Exception as e:
        logger.error("Error fetching job output: %s\n%s", e, traceback.format_exc())
        raise

    path = f"{username}/{filename}.png"
    url = upload_to_bucket(bucket, path, content)
    return url