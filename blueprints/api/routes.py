# api/routes.py
from flask import Blueprint, request, jsonify
from utils.supabase_helpers import mark_job_complete, return_user
from utils.vast_helpers import get_instance_info, view_request

api_bp = Blueprint("api", __name__)

@api_bp.route("/api/check_job", methods=["POST"])
def check_job():
    job = request.get_json()
    user_email = job["email"]
    filename = job["filename"]

    user = return_user(user_email)

    server_id = user.app_metadata.get("server_id")

    inst = get_instance_info(server_id)
    cookies = {f"C.{server_id}_auth_token": inst["token"]}
    base_url = f"http://{inst['ip_address']}:{inst['port']}/api"

    url = view_request(user_email, filename, cookies, base_url)

    if url:
        mark_job_complete(user_email, filename, url)
    return jsonify({"status": "ok"})