from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from utils.workflow import build_payload
from utils.supabase_helpers import add_pending_job
from extensions import supabase, supabase_admin
from utils.vast_helpers import get_instance_info
import logging, traceback, httpx
from functools import wraps

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id", False):
            return redirect(url_for("auth.login"))

        try:
            user_id = session["user_id"]
            user = supabase_admin.auth.admin.get_user_by_id(user_id).user
            if not user:
                session.clear()
                return redirect(url_for("auth.login"))
        except Exception as e:
            print(f"An unexpected error occurred during session validation: {e}")
            session.clear()
            return redirect(url_for("auth.login"))

        return f(user.user_metadata, *args, **kwargs)

    return decorated_function


@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def dashboard(user):
    if request.method == "POST":
        server_id = user.get("server_id")
        prompt = request.form.get("prompt")
        filename = request.form.get("filename")

        try:
            inst = get_instance_info(server_id)
            cookies = {f"C.{server_id}_auth_token": inst["token"]}
            base_url = f"http://{inst['ip_address']}:{inst['port']}/api"
            headers = {"Content-Type": "application/json", "Accept": "*/*"}

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
            print(f"Error during image generation: {e}", flush=True)
            flash("Failed to generate image.", "danger")

        return redirect(url_for("dashboard.dashboard"))

    # GET
    server_id = user.get("server_id")
    email_verified = user.get("email_verified")

    try:
        response = (
            supabase.table("jobs")
            .select("*")
            .eq("email", session["user"])
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        last_jobs = response.data if response.data else []
    except Exception:
        last_jobs = []
        flash("Could not load jobs.", "danger")

    return render_template(
        "dashboard/dashboard.html",
        user=user,
        last_jobs=last_jobs,
        restricted=(not server_id or not email_verified),
    )


@dashboard_bp.route("/jobs", methods=["GET", "POST"])
@login_required
def dashboard_jobs(user):
    if request.method == "POST":
        action = request.form.get("action")
        page = session.get("page", 0)

        if action == "next":
            session["page"] = page + 1
        elif action == "prev" and page > 0:
            session["page"] = page - 1
        elif action == "first":
            session["page"] = 0

        return redirect(url_for("dashboard.dashboard_jobs"))

    # GET
    page = session.get("page", 0)
    page_size = 10

    response = (
        supabase.table("jobs").select("status").eq("email", session["user"]).execute()
    )
    jobs = response.data if response else []

    pending_jobs = len([job for job in jobs if job["status"] is False])
    done_jobs = len(jobs) - pending_jobs

    response = (
        supabase.table("jobs")
        .select("*")
        .eq("email", session["user"])
        .range(page * page_size, (page + 1) * page_size)
        .order("created_at", desc=True)
        .execute()
    )
    jobs = response.data if response.data else []

    if len(jobs) > page_size:
        jobs = jobs[:page_size]
        has_next_page = True
    else:
        has_next_page = False

    return render_template(
        "dashboard/jobs.html",
        jobs=jobs,
        pending_jobs=pending_jobs,
        done_jobs=done_jobs,
        page=page,
        has_next_page=has_next_page,
        user=user,
    )


@dashboard_bp.route("/profile", methods=["GET"])
@login_required
def dashboard_user(user):
    return render_template("dashboard/profile.html", user=user)


@dashboard_bp.route("/reset_password", methods=["POST"])
def dashboard_reset():
    password = request.form.get("password")
    try:
        supabase.auth.update_user({"password": password})
        flash("Password reset succesfully.", "reset_success")
    except Exception as e:
        print(str(e))
        flash(str(e), "reset_danger")
    return redirect(url_for("dashboard.dashboard_user"))
