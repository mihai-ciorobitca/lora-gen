from requests import get
import traceback
from extensions import logger
from .supabase_helpers import get_pending_jobs, add_to_history
from .storage import upload_to_bucket
from .supabase_helpers import return_user
from .vast_helpers import get_instance_info

def process_pending_jobs(user_email):
    user = return_user(user_email)
    server_id = user.app_metadata.get("server_id") if user.app_metadata else None

    headers = {"Content-Type": "application/json", "Accept": "*/*"}

    if not server_id:
        logger.warning("No server_id found for %s", user_email)
        return

    try:
        inst = get_instance_info(server_id)
        token, ip, port = inst["token"], inst["ip_address"], inst["port"]
        cookies = {f"C.{server_id}_auth_token": token}
        base_url = f"http://{ip}:{port}/api"

        pending = get_pending_jobs(user_email)
        for job in pending:
            filename, prompt = job["filename"], job["prompt"]

            hist_resp = get(f"{base_url}/history?max_items=20", cookies=cookies, headers=headers)
            if hist_resp.status_code != 200:
                continue

            hist_data = hist_resp.json()
            found = False
            for _, job_data in hist_data.items():
                outputs = job_data.get("outputs", {})
                if "10" in outputs:
                    for img in outputs["10"].get("images", []):
                        if filename in img["filename"]:
                            found = True
                            payload = {"filename": filename, "type": "output", "subfolder": user_email}
                            view_resp = get(f"{base_url}/view", params=payload, cookies=cookies, headers=headers)
                            if view_resp.status_code == 200 and view_resp.content:
                                img_bytes = view_resp.content
                                storage_path = f"{user_email}/{filename}.png"
                                url = upload_to_bucket("generated_images", storage_path, img_bytes)
                                add_to_history(user_email, prompt, filename, url)

            if not found:
                logger.info("Job %s still pending", filename)

    except Exception as e:
        logger.error("Error processing pending jobs for %s: %s\n%s", user_email, e, traceback.format_exc())
