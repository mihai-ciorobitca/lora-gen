from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from extensions import supabase_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")



def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "is_admin" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/")
@login_required
def dashboard():
    response = supabase_admin.auth.admin.list_users()
    return render_template("admin.html", users=response)


@admin_bp.route("/toggle_verify", methods=["POST"])
def toggle_verify():
    if not session.get("is_admin", False):
        return redirect(url_for("auth.login"))
    user_id = request.form["user_id"]
    user = supabase_admin.auth.admin.get_user_by_id(user_id).user
    verified = user.user_metadata.get("email_verified", False)
    supabase_admin.auth.admin.update_user_by_id(
        user_id, {"user_metadata": {"email_verified": not verified}}
    )
    flash("User verification updated.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/update_server_id", methods=["POST"])
def update_server_id():
    if not session.get("is_admin", False):
        return redirect(url_for("auth.login"))
    user_id = request.form.get("user_id")
    server_id = request.form.get("server_id")

    try:
        supabase_admin.auth.admin.update_user_by_id(
            user_id, {"app_metadata": {"server_id": server_id}}
        )
        flash("Server ID updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating server ID: {str(e)}", "danger")

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete_user", methods=["POST"])
def delete_user():
    if not session.get("is_admin", False):
        return redirect(url_for("auth.login"))
    user_id = request.form.get("user_id")
    try:
        supabase_admin.auth.admin.delete_user(user_id)
        flash("User deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))
