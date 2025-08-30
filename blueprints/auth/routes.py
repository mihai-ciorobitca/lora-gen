from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os, requests, urllib.parse
from extensions import supabase
from utils.supabase_helpers import user_exists

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

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
            resp = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
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
    res = supabase.auth.sign_in_with_oauth({"provider": "google"})
    return redirect(res.url)


@auth_bp.route("/save_session", methods=["POST"])
def save_session():
    data = request.json
    if not data:
        return {"error": "no session"}, 400

    session["access_token"] = data.get("access_token")
    session["refresh_token"] = data.get("refresh_token")
    session["user"] = data.get("user", {}).get("email")
    return {"status": "ok"}
