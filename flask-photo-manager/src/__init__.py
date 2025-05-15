from flask import Flask

def create_app():
    app = Flask(__name__)
    
    with app.app_context():
        from . import app as main_app
        app.register_blueprint(main_app.bp)

    return app