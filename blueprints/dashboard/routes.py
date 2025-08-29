from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import httpx, traceback, logging
from utils.workflow import build_payload
from utils.supabase_helpers import (
    get_history,
    get_pending_jobs,
    add_pending_job,
    return_user,
)
from utils.vast_helpers import get_instance_info

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard_home():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    user_email = session["user"]
    user = return_user(user_email)
    server_id = user.app_metadata.get("server_id") if user.app_metadata else None

    if not server_id:
        return render_template("dashboard.html", user=user, restricted=True)

    if request.method == "POST":
        prompt = request.form.get("prompt")
        filename = request.form.get("filename")
        try:
            inst = get_instance_info(server_id)
            cookies = {f"C.{server_id}_auth_token": inst["token"]}
            base_url = f"http://{inst['ip_address']}:{inst['port']}/api"
            headers = {"Content-Type": "application/json", "Accept": "*/*"}

            payload = build_payload(user.email, filename, prompt)
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{base_url}/prompt", json=payload, cookies=cookies, headers=headers)
                resp.raise_for_status()
            
            prompt_id = resp.json().get("prompt_id")

            add_pending_job(user.email, prompt, filename, prompt_id)
            flash("Job submitted successfully.", "success")

        except Exception as e:
            logging.error("Image generation failed: %s\n%s", e, traceback.format_exc())
            flash("Failed to generate image.", "danger")

    return render_template("dashboard.html", user=user)

@dashboard_bp.route("/dashboard/pending")
def dashboard_pending():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    pending_images = get_pending_jobs(session["user"])
    return render_template("dashboard.html", pending_images=pending_images)


@dashboard_bp.route("/dashboard/history")
def dashboard_history():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    history = get_history(session["user"])
    return render_template("dashboard.html", history=history)

@dashboard_bp.route("/dashboard/account")
def dashboard_account():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    user = return_user(session["user"])
    return render_template("dashboard.html", user=user)


@dashboard_bp.route("/dashboard/settings")
def dashboard_settings():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html")