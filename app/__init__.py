from flask import Flask

def create_app():
    app = Flask(__name__)
    
    from .routes import convert_bp
    app.register_blueprint(convert_bp)

    @app.route('/health')
    def health_check():
        return 'OK', 200

    return app
