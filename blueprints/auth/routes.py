from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import supabase
from utils.supabase_helpers import user_exists
from os import getenv
from requests import post

ADMIN_EMAIL = getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD")
HCAPTCHA_SITE_KEY = getenv("HCAPTCHA_SITE_KEY")
HCAPTCHA_SECRET = getenv("HCAPTCHA_SECRET")


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login_get():
    if "user" in session:
        return redirect(url_for("dashboard.dashboard_get"))
    return render_template("auth/login.html", HCAPTCHA_SITE_KEY=HCAPTCHA_SITE_KEY)


@auth_bp.post("/login")
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")
    hcaptcha_token = request.form.get("h-captcha-response")

    verify_url = "https://hcaptcha.com/siteverify"
    payload = {
        "secret": HCAPTCHA_SECRET,
        "response": hcaptcha_token,
        "remoteip": request.remote_addr,
    }
    resp = post(verify_url, data=payload).json()
    print(resp)

    if not resp.get("success"):
        flash("Captcha verification failed. Try again.", "login_danger")
        return redirect(url_for("auth.login_get"))

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
    return redirect(url_for("auth.login_get"))


@auth_bp.get("/register")
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
    return redirect(url_for("auth.login_get"))


@auth_bp.route("/login/google")
def login_google():
    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {
                    "redirect_to": url_for("auth.google_callback", _external=True),
                    "query_params": {"prompt": "select_account"},
                },
            }
        )
        return redirect(response.url)
    except Exception as e:
        print(str(e))
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


@auth_bp.get("/reset")
def reset_get():
    token = request.args.get("token")
    if not token:
        flash("Invalid or missing token.", "login_danger")
        return redirect(url_for("auth.login_get"))

    return render_template("auth/reset.html", token=token)


@auth_bp.post("/reset")
def reset_post():
    new_password = request.form.get("new_password")
    token = request.form.get("token")

    if not new_password or len(new_password) < 6:
        flash("Password must be at least 6 characters long.", "login_danger")
        return redirect(request.url)

    if not token:
        flash("Missing reset token.", "login_danger")
        return redirect(url_for("auth.login_get"))

    try:
        supabase.auth.update_user(
            {"password": new_password},
            token=token
        )
        flash("Password reset successfully ✅", "login_success")
        return redirect(url_for("auth.login_get"))

    except Exception as e:
        flash(f"Something went wrong while resetting password: {str(e)}", "login_danger")
        return redirect(url_for("auth.login_get"))


@auth_bp.get("/recovery")
def recovery_get():
    return render_template("auth/recovery.html")


@auth_bp.post("/recovery")
def recovery_post():
    email = request.form.get("email")
    if not email:
        flash("Please provide your email.", "error")
        return redirect(url_for("auth.recovery"))

    try:
        supabase.auth.reset_password_for_email(
            email,
            {"redirect_to": url_for("auth.reset_get", token="{token}", _external=True)}
        )
        flash("Check your email for the password reset link!", "login_success")
        return redirect(url_for("auth.login_get"))
    except Exception as e:
        flash(f"Failed to send reset email: {str(e)}", "error")
        return redirect(url_for("auth.recovery"))