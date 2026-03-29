import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = FastAPI()

    # Configure Logging
    logging.basicConfig(level=logging.INFO)

    # Middleware / CORS Setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Content-Type"],
        expose_headers=["Set-Cookie"],
    )

    from .routes import get_routers
    for router in get_routers():
        app.include_router(router, prefix="/api")

    return app
