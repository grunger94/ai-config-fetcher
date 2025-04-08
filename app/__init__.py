from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    from app.routes import configure_routes
    configure_routes(app)

    return app
