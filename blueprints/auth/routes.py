from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import supabase, cache
from utils.supabase_helpers import user_exists
from os import getenv

ADMIN_EMAIL = getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD")

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
@cache.cached(timeout=3600)
def login_get():
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin.dashboard"))

    try:
        resp = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        print(resp)
        user, session_data = resp.user, resp.session
        if user and session_data:
            session["user"] = user.email
            session["user_id"] = user.id
            print(session["user_id"])
            flash("Login successful!", "login_success")
            return redirect(url_for("dashboard.dashboard_get"))
        flash("Login failed. Please check credentials.", "login_danger")

    except Exception as e:
        flash(f"Login failed: {str(e)}", "login_danger")
    return render_template("auth/login.html")


@auth_bp.get("/register")
@cache.cached(timeout=3600)
def register_get():
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_post():
    email = request.form.get("email")
    password = request.form.get("password")
    fname = request.form.get("fname")
    lname = request.form.get("lname")

    if user_exists(email):
        flash("This email is already registered. Please log in.", "danger")
        return render_template("auth/register.html")

    try:
        resp = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "server_id": None,
                        "full_name": f"{fname} {lname}",
                    },
                    "email_redirect_to": "https://lora-gen.onrender.com/auth/login",
                },
            }
        )
        print(resp)
        user, session_data = resp.user, resp.session
        if user and session_data:
            session["user"] = user.email
            session["user_id"] = user.id
            flash("Registration successful!", "register_success")
            return redirect(url_for("dashboard.dashboard"))

        flash("Please confirm your email.", "register_warning")
        return redirect(url_for("auth.login_get"))
    except Exception as e:
        flash(f"Registration failed: {str(e)}", "register_danger")
        return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@auth_bp.route("/login/google")
def login_google():
    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {
                    "redirect_to": url_for("auth.google_callback", _external=True)
                },
            }
        )
        return redirect(response.get("url"))
    except Exception as e:
        flash(f"Google login setup failed: {str(e)}", "danger")
        return redirect(url_for("auth.login_get"))


@auth_bp.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    next_url = request.args.get("next", url_for("dashboard.dashboard_get"))

    if not code:
        flash("Google login failed. No authorization code.", "danger")
        return redirect(url_for("auth.login_get"))

    try:
        response = supabase.auth.exchange_code_for_session({"auth_code": code})

        if not response.user:
            flash("Google login failed: no user returned", "danger")
            return redirect(url_for("auth.login_get"))

        user = response.user
        session["user"] = user.email
        session["user_id"] = user.id

        flash("Logged in successfully with Google! 🎉", "success")
        return redirect(next_url)

    except Exception as e:
        flash(f"Google login failed: {str(e)}", "danger")
        return redirect(url_for("auth.login_get"))



@auth_bp.route("/reset_password", methods=["POST"])
def reset_password():
    if "user" not in session:
        flash("You must be logged in to reset your password.", "error")
        return redirect(url_for("auth.login"))

    new_password = request.form.get("new_password")

    if not new_password or len(new_password) < 6:
        flash("Password must be at least 6 characters long.", "error")
        return redirect(url_for("dashboard.dashboard_settings"))

    try:
        user = supabase.auth.get_user(session["access_token"]).user

        if not user:
            flash("User not found.", "error")
            return redirect(url_for("dashboard.dashboard_settings"))

        supabase.auth.update_user({"password": new_password})

        flash("Password reset successfully ✅", "success")
        return redirect(url_for("dashboard.dashboard_settings"))

    except Exception as e:
        flash("Something went wrong while resetting password.", "error")
        return redirect(url_for("dashboard.dashboard_settings"))
