from flask import Flask, render_template
from extensions import cache
from blueprints.auth.routes import auth_bp
from blueprints.dashboard.routes import dashboard_bp
from blueprints.admin.routes import admin_bp
from blueprints.api.routes import api_bp
import os

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config["CACHE_TYPE"] = "simple"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    app.secret_key = os.getenv("FLASK_KEY")

    cache.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route("/")
    @cache.cached()
    @cache.cached(timeout=3600)
    def index():
        return render_template("index.html")

    @app.route("/pricing")
    @cache.cached()
    @cache.cached(timeout=3600)
    def pricing():
        return render_template("pricing.html")
    
    @app.errorhandler(404)
    @cache.cached()
    @cache.cached(timeout=3600)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(405)
    @cache.cached(timeout=3600)
    def method_not_allowed(e):
        return render_template("405.html"), 405

    @app.errorhandler(500)
    @cache.cached(timeout=3600)
    def server_error(e):
        return render_template("500.html"), 500
    
    @app.route("/health")
    @cache.cached(timeout=0)
    def health_check():
        return "OK", 200

    return app


app = create_app()
