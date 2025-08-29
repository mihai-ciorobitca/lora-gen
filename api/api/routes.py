# api/routes.py
from flask import Blueprint, jsonify
import logging, traceback
from utils.supabase_helpers import get_all_pending_jobs, mark_job_complete, return_user
from utils.vast_helpers import get_instance_info, view_request

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/check_jobs", methods=["GET"])
def check_jobs():
    updated = []
    errors = []

    try:
        pending_jobs = get_all_pending_jobs()

        for job in pending_jobs:
            try:
                user_email = job["email"]
                filename = job["filename"]

                user = return_user(user_email)
                if not user or not user.app_metadata:
                    continue

                server_id = user.app_metadata.get("server_id")
                if not server_id:
                    continue

                inst = get_instance_info(server_id)
                cookies = {f"C.{server_id}_auth_token": inst["token"]}
                base_url = f"http://{inst['ip_address']}:{inst['port']}/api"

                # Ask Vast API if the image is ready
                url = view_request(user_email, filename, cookies, base_url)

                if url:
                    mark_job_complete(user_email, filename, url)
                    updated.append(
                        {"email": user_email, "filename": filename, "url": url}
                    )

            except Exception as e:
                logging.error("Job check failed: %s\n%s", e, traceback.format_exc())
                errors.append(
                    {"filename": job.get("filename"), "error": str(e)}
                )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok", "updated": updated, "errors": errors})
