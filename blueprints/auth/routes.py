from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os, requests, urllib.parse
from extensions import supabase
from utils.supabase_helpers import user_exists

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")  # public anon key, not service key

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ----------------- Email/Password Login -----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))

        try:
            resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user, session_data = resp.user, resp.session
            if user and session_data:
                session["user"] = user.email
                session["access_token"] = session_data.access_token
                return redirect(url_for("dashboard.dashboard_home"))
            flash("Login failed. Please check credentials.", "danger")
        except Exception as e:
            flash(f"Login failed: {str(e)}", "danger")

    return render_template("login.html")


# ----------------- Email/Password Register -----------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if user_exists(email):
            flash("This email is already registered. Please log in.", "danger")
            return render_template("register.html")

        try:
            resp = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"server_id": None}},
                }
            )
            user, session_data = resp.user, resp.session
            if user and session_data:
                session["user"] = user.email
                session["access_token"] = session_data.access_token
                flash("Registration successful!", "success")
                return redirect(url_for("dashboard.dashboard_home"))

            flash("Please confirm your email.", "warning")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")

    return render_template("register.html")


# ----------------- Logout -----------------
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


# ----------------- Google OAuth -----------------
@auth_bp.route("/login/google")
def login_google():
    # Redirect user to Supabase's Google OAuth page
    redirect_uri = url_for("auth.callback", _external=True)
    params = {
        "provider": "google",
        "redirect_to": redirect_uri,
    }
    # Supabase provides an auth/v1/authorize endpoint
    url = f"{SUPABASE_URL}/auth/v1/authorize?{urllib.parse.urlencode(params)}"
    return redirect(url)


@auth_bp.route("/callback")
def callback():
    """
    This route is called after Google login.
    Supabase will redirect here with a code (authorization code).
    We need to exchange it for a session (access + refresh token).
    """
    error = request.args.get("error")
    if error:
        flash(f"Google login failed: {error}", "danger")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    if not code:
        flash("Missing authorization code.", "danger")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.callback", _external=True)

    # Exchange authorization code for a session
    token_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=authorization_code"
    headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    payload = {"code": code, "redirect_uri": redirect_uri}

    r = requests.post(token_url, headers=headers, json=payload)

    if r.status_code != 200:
        flash("Google login failed. Could not get session.", "danger")
        return redirect(url_for("auth.login"))

    data = r.json()
    # Save session in Flask
    session["access_token"] = data.get("access_token")
    session["refresh_token"] = data.get("refresh_token")

    # Get user info
    user_info_url = f"{SUPABASE_URL}/auth/v1/user"
    user_headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {session['access_token']}"}
    u = requests.get(user_info_url, headers=user_headers)
    user_data = u.json()

    session["user"] = user_data.get("email")

    flash("Google login successful!", "success")
    return redirect(url_for("dashboard.dashboard_home"))
