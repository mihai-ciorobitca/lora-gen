from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from utils.workflow import build_payload
from utils.supabase_helpers import (
    add_pending_job,
)
from extensions import supabase
from utils.vast_helpers import get_instance_info
import logging, traceback, httpx

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_get"))
        return f(*args, **kwargs)

    return decorated_function


@dashboard_bp.get("/")
@login_required
def dashboard_get():
    try:
        user = supabase.auth.get_user(session["access_token"]).user
    except Exception as e:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login_get"))

    server_id = user.app_metadata.get("server_id") if user.app_metadata else False

    try:
        response = (
            supabase.table("jobs")
            .select("*")
            .eq("email", session["user"])
            .order("created_at", desc=True)
            .execute()
        )
        jobs = response.data if response.data else []
        print(f"Jobs for {session['user']}: {jobs}", flush=True)
    except Exception as e:
        jobs = []
        flash("Could not load jobs.", "danger")
        print(f"Error fetching jobs: {e}")

    return render_template(
        "dashboard/dashboard.html", user=user, jobs=jobs, restricted=not server_id
    )


@dashboard_bp.post("/")
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


@dashboard_bp.get("/jobs")
@login_required
def dasboard_jobs():
    try:
        supabase.auth.get_user(session["access_token"]).user
    except Exception as e:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login_get"))
    response = (
        supabase.table("jobs")
        .select("*")
        #.eq("email", session["user"])
        .order("created_at", desc=True)
        .execute()
    )
    jobs = response.data if response.data else []
    print(f"Jobs for {session['user']}: {jobs}", flush=True)
    total_jobs = len(jobs)
    pending_jobs = len([job for job in jobs if job["status"] == False])
    done_jobs = len([job for job in jobs if job["status"] == True])
    return render_template(
        "dashboard/jobs.html",
        jobs=jobs,
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        done_jobs=done_jobs,
    )
