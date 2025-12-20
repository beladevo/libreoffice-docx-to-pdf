from flask import Flask
from .routes import convert_bp
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s",
        force=True,  # ⬅ override Flask & Gunicorn
    )

def create_app():
    setup_logging()  

    app = Flask(__name__)
    app.register_blueprint(convert_bp)

    @app.route("/health")
    def health():
        return "OK", 200

    return app