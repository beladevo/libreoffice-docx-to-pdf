from flask import Flask
from .routes import convert_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(convert_bp)

    return app
