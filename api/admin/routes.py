from flask import Blueprint, render_template, redirect, url_for, request, flash
from extensions import supabase

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def dashboard():
    response = supabase.auth.admin.list_users()
    return render_template("admin.html", users=response)


@admin_bp.route("/toggle_verify", methods=["POST"])
def toggle_verify():
    user_id = request.form["user_id"]
    user = supabase.auth.admin.get_user_by_id(user_id).user
    verified = user.user_metadata.get("email_verified", False)
    supabase.auth.admin.update_user_by_id(
        user_id, {"user_metadata": {"email_verified": not verified}}
    )
    flash("User verification updated.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/update_server_id", methods=["POST"])
def update_server_id():
    user_id = request.form.get("user_id")
    server_id = request.form.get("server_id")

    try:
        supabase.auth.admin.update_user_by_id(
            user_id, {"app_metadata": {"server_id": server_id}}
        )
        flash("Server ID updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating server ID: {str(e)}", "danger")

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete_user", methods=["POST"])
def delete_user():
    user_id = request.form.get("user_id")
    try:
        supabase.auth.admin.delete_user(user_id)
        flash("User deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))
