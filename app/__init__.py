import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Configure Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Middleware / CORS Setup
    CORS(app, resources={r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5000",
            "*" #remove this in production environment (FIXME)
        ],
        "supports_credentials": True
    }})

    from .routes import register_blueprints
    register_blueprints(app)

    return app
