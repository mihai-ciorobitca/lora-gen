from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from extensions import supabase_admin
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def login_required_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "is_admin" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/", methods=["GET", "POST"])
@login_required_admin
def dashboard():
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")

        try:
            if action == "toggle_verify":
                verified_str = request.form.get("verified")
                verified = verified_str == "true"
                supabase_admin.auth.admin.update_user_by_id(
                    user_id, {"user_metadata": {"email_verified": not verified}}
                )
                flash("User verification updated.", "success")

            elif action == "update_server_id":
                server_id = request.form.get("server_id")
                supabase_admin.auth.admin.update_user_by_id(
                    user_id, {"user_metadata": {"server_id": server_id}}
                )
                flash("Server ID updated successfully!", "success")

            elif action == "delete_user":
                supabase_admin.auth.admin.delete_user(user_id)
                flash("User deleted successfully.", "success")

        except Exception as e:
            flash(f"Error performing {action}: {str(e)}", "danger")

        return redirect(url_for("admin.dashboard"))

    # GET
    response = supabase_admin.auth.admin.list_users()
    return render_template("admin/admin.html", users=response)
