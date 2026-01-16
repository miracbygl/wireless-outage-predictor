from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'lopy4-rssi-monitor-secret'

    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    from .routes import main_bp
    app.register_blueprint(main_bp)

    from . import events  # noqa: F401

    return app
