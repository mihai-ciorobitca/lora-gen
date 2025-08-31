from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from utils.workflow import build_payload
from utils.supabase_helpers import (
    add_pending_job,
)
from extensions import supabase
from utils.vast_helpers import get_instance_info
import logging, traceback, httpx

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_get"))
        return f(*args, **kwargs)

    return decorated_function



@dashboard_bp.get("/dashboard")
@login_required
def dashboard_get():
    try:
        user = supabase.auth.get_user(session["access_token"]).user
    except Exception as e:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login_get"))
    server_id = user.app_metadata.get("server_id") if user.app_metadata else None

    if not server_id:
        return render_template("dashboard.html", user=user, restricted=True)

    return render_template("dashboard.html", user=user)

@dashboard_bp.post("/dashboard")
@login_required
def dashboard_post():
    user = supabase.auth.get_user(session["access_token"]).user
    server_id = user.app_metadata.get("server_id") if user.app_metadata else None

    prompt = request.form.get("prompt")
    filename = request.form.get("filename")
    
    try:
        inst = get_instance_info(server_id)
        cookies = {f"C.{server_id}_auth_token": inst["token"]}
        base_url = f"http://{inst['ip_address']}:{inst['port']}/api"
        headers = {"Content-Type": "application/json", "Accept": "*/*"}

        print(cookies, base_url, headers)

        payload = build_payload(user.email, filename, prompt)
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{base_url}/prompt", json=payload, cookies=cookies, headers=headers
            )
            resp.raise_for_status()

        prompt_id = resp.json().get("prompt_id")

        add_pending_job(user.email, prompt, filename, prompt_id)
        flash("Job submitted successfully.", "success")

    except Exception as e:
        logging.error("Image generation failed: %s\n%s", e, traceback.format_exc())
        flash("Failed to generate image.", "danger")
