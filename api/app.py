from flask import Flask, render_template
from extensions import logger
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from admin.routes import admin_bp
from api.routes import api_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "dev_secret_key"

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/pricing")
    def pricing():
        return render_template("pricing.html")
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template("405.html"), 405

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server Error: {e}")
        return render_template("500.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=3000)
