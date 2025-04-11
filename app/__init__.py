from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.routes import configure_routes

def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)
    configure_routes(app)

    return app
