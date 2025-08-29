from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import supabase
from utils.supabase_helpers import user_exists

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user, session_data = resp.user, resp.session
            if user and session_data:
                session["user"] = user.email
                session["access_token"] = session_data.access_token
                return redirect(url_for("dashboard.dashboard"))
            flash("Login failed. Please check credentials.", "danger")
        except Exception as e:
            flash(f"Login failed: {str(e)}", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if user_exists(email):
            flash("This email is already registered. Please log in.", "danger")
            return render_template("register.html")

        try:
            resp = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"server_id": None}}})
            user, session_data = resp.user, resp.session
            if user and session_data:
                session["user"] = user.email
                session["access_token"] = session_data.access_token
                flash("Registration successful!", "success")
                return redirect(url_for("dashboard.dashboard"))
            flash("Please confirm your email.", "warning")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")

    return render_template("register.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))
